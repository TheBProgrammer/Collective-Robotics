-- Normal robot controller.
-- Two-state FSM (WANDER / STOPPED) for aggregation; listens for "leave"
-- broadcasts from anti-agents and resumes wandering when ordered.

local MAX_VELOCITY  = 20      -- cm/s
local STOP_DISTANCE = 25      -- cm   : RAB distance that triggers STOP
local WAIT_TICKS    = 30      -- 3.0 s
local TURN_GAIN     = 2.0
local LOG_INTERVAL  = 5       -- ticks
local ANTI_RANGE    = 60      -- cm   : only obey leave orders from anti-agents within this range

-- RAB byte layout: [1]=agent_type (0 normal, 1 anti), [2]=leave_flag, [3]=stopped
local TYPE_NORMAL = 0
local TYPE_ANTI   = 1

local state = "WANDER"
local timer = 0
local tick_count = 0

function init()
    reset()
end

function step()
    tick_count = tick_count + 1

    -- Tag outgoing broadcasts so anti-agents can identify clusters of normals.
    robot.range_and_bearing.set_data(1, TYPE_NORMAL)
    robot.range_and_bearing.set_data(2, 0)
    robot.range_and_bearing.set_data(3, (state == "STOPPED") and 1 or 0)

    local msgs = robot.range_and_bearing
    local near_count = 0
    local detected   = false
    local leave_order = false

    for i = 1, #msgs do
        local r  = msgs[i].range
        local d  = msgs[i].data
        local is_anti = (d[1] == TYPE_ANTI)
        if not is_anti and r < STOP_DISTANCE then
            detected   = true
            near_count = near_count + 1
        end
        -- Anti-agent leave order
        if is_anti and d[2] == 1 and r < ANTI_RANGE then
            leave_order = true
        end
    end

    if state == "WANDER" then
        robot.leds.set_all_colors("green")
        if detected then
            state = "STOPPED"
            timer = WAIT_TICKS
            robot.wheels.set_velocity(0, 0)
        else
            obstacle_avoidance_move()
        end

    elseif state == "STOPPED" then
        robot.leds.set_all_colors("red")
        robot.wheels.set_velocity(0, 0)
        timer = timer - 1
        if leave_order then
            -- Forced to leave: skip timer, scatter immediately for a few ticks.
            state = "LEAVING"
            timer = 10
            robot.leds.set_all_colors("yellow")
        elseif timer <= 0 then
            state = "WANDER"
        end

    elseif state == "LEAVING" then
        -- Brief forced-wander phase: ignore stop triggers so the robot escapes the cluster.
        robot.leds.set_all_colors("yellow")
        obstacle_avoidance_move()
        timer = timer - 1
        if timer <= 0 then
            state = "WANDER"
        end
    end

    if tick_count % LOG_INTERVAL == 0 then
        local pos = robot.positioning.position
        local stopped_flag = (state == "STOPPED") and 1 or 0
        -- DATA,<role>,<id>,<tick>,<x>,<y>,<neighbors>,<stopped>
        log(string.format("DATA,N,%s,%d,%.3f,%.3f,%d,%d",
            robot.id, tick_count, pos.x, pos.y, near_count, stopped_flag))
    end
end

function obstacle_avoidance_move()
    local sum_x, sum_y = 0.0, 0.0
    for i = 1, #robot.proximity do
        local v = robot.proximity[i].value
        local a = robot.proximity[i].angle
        sum_x = sum_x - v * math.cos(a)
        sum_y = sum_y - v * math.sin(a)
    end
    local mag = math.sqrt(sum_x*sum_x + sum_y*sum_y)
    if mag < 0.05 then
        robot.wheels.set_velocity(MAX_VELOCITY, MAX_VELOCITY)
    else
        local steer = math.atan2(sum_y, sum_x)
        local lv = MAX_VELOCITY - TURN_GAIN * steer
        local rv = MAX_VELOCITY + TURN_GAIN * steer
        lv = math.max(-MAX_VELOCITY, math.min(MAX_VELOCITY, lv))
        rv = math.max(-MAX_VELOCITY, math.min(MAX_VELOCITY, rv))
        robot.wheels.set_velocity(lv, rv)
    end
end

function reset()
    state = "WANDER"
    timer = 0
    tick_count = 0
    robot.wheels.set_velocity(0, 0)
end

function destroy() end
