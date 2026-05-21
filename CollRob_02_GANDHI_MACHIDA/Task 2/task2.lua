-- Tunable Parameters
local MAX_VELOCITY  = 20    -- cm/s  : forward speed while wandering
local STOP_DISTANCE = 25    -- cm    : RAB range threshold to stop
local WAIT_TICKS    = 30    -- ticks : how long to stay stopped
local TURN_GAIN     = 2.0   --       : steering gain for obstacle avoidance
local LOG_INTERVAL  = 5     -- ticks : data logging frequency

-- Internal State
local state = "WANDER"
local timer = 0
local tick_count = 0

function init()
    reset()
end

function step()
    tick_count = tick_count + 1

    -- count neighbors within stop distance
    local neighbors  = robot.range_and_bearing
    local near_count = 0
    local detected   = false

    for i = 1, #neighbors do
        if neighbors[i].range < STOP_DISTANCE then
            detected  = true
            near_count = near_count + 1
        end
    end

    -- State Machine
    if state == "WANDER" then
        robot.leds.set_all_colors("green")

        if detected then
            -- A neighbor is close: stop and wait
            state = "STOPPED"
            timer = WAIT_TICKS
            robot.wheels.set_velocity(0, 0)
        else
            -- No neighbor nearby
            obstacle_avoidance_move()
        end

    elseif state == "STOPPED" then
        robot.leds.set_all_colors("red")
        robot.wheels.set_velocity(0, 0)

        timer = timer - 1
        if timer <= 0 then
            state = "WANDER"
        end
    end

    -- Data Logging
    -- Format: DATA,<id>,<tick>,<near_neighbors>,<stopped 0|1>
    if tick_count % LOG_INTERVAL == 0 then
        local stopped_flag = (state == "STOPPED") and 1 or 0
        log(string.format("DATA,%s,%d,%d,%d",
            robot.id, tick_count, near_count, stopped_flag))
    end
end

-- Vector-based obstacle avoidance using all 24 proximity sensors
function obstacle_avoidance_move()
    local sum_x = 0.0
    local sum_y = 0.0

    for i = 1, #robot.proximity do
        local v = robot.proximity[i].value
        local a = robot.proximity[i].angle
        -- Repulsion: push away from obstacle
        sum_x = sum_x - v * math.cos(a)
        sum_y = sum_y - v * math.sin(a)
    end

    local magnitude = math.sqrt(sum_x * sum_x + sum_y * sum_y)

    if magnitude < 0.05 then
        -- No significant obstacle - drive straight
        robot.wheels.set_velocity(MAX_VELOCITY, MAX_VELOCITY)
    else
        -- Steer toward the avoidance vector direction
        -- steer > 0: avoidance is left -> slow left wheel, speed right
        -- steer < 0: avoidance is right -> slow right wheel, speed left
        local steer = math.atan2(sum_y, sum_x)
        local lv = MAX_VELOCITY - TURN_GAIN * steer
        local rv = MAX_VELOCITY + TURN_GAIN * steer

        -- Clamp to valid velocity range
        lv = math.max(-MAX_VELOCITY, math.min(MAX_VELOCITY, lv))
        rv = math.max(-MAX_VELOCITY, math.min(MAX_VELOCITY, rv))
        robot.wheels.set_velocity(lv, rv)
    end
end

function reset()
    state      = "WANDER"
    timer      = 0
    tick_count = 0
    robot.wheels.set_velocity(0, 0)
end

function destroy()
end