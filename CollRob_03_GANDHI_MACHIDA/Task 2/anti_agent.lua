-- Anti-agent controller.
-- Never stops; wanders around. When it observes a cluster of STOPPED normal
-- robots whose size exceeds CLUSTER_THRESHOLD, it broadcasts a "leave" order
-- via RAB. Robots within ANTI_RANGE will then evacuate. This is the
-- swarm-controlled emergence mechanism of Scheidler/Merkle adapted to
-- swarm aggregation.

local MAX_VELOCITY        = 20    -- cm/s
local TURN_GAIN           = 2.0
local SCAN_RANGE          = 60    -- cm  : range within which we count stopped neighbours
local CLUSTER_THRESHOLD   = 3     -- minimum stopped neighbours to issue a leave order
local TURN_PROB           = 0.02  -- random reorientation probability per tick
local LOG_INTERVAL        = 5

local TYPE_NORMAL = 0
local TYPE_ANTI   = 1

local tick_count = 0
local turn_timer = 0

function init()
    reset()
end

function step()
    tick_count = tick_count + 1

    -- 1) Inspect neighbours: count stopped normal robots inside SCAN_RANGE.
    local msgs = robot.range_and_bearing
    local stopped_near = 0
    for i = 1, #msgs do
        local d = msgs[i].data
        local r = msgs[i].range
        if d[1] == TYPE_NORMAL and d[3] == 1 and r < SCAN_RANGE then
            stopped_near = stopped_near + 1
        end
    end

    -- 2) Decide whether to issue a "leave" order.
    local issue_leave = (stopped_near >= CLUSTER_THRESHOLD)
    robot.range_and_bearing.set_data(1, TYPE_ANTI)
    robot.range_and_bearing.set_data(2, issue_leave and 1 or 0)
    robot.range_and_bearing.set_data(3, 0)

    -- 3) LED colour: blue normally, magenta when broadcasting a leave order.
    if issue_leave then
        robot.leds.set_all_colors("magenta")
    else
        robot.leds.set_all_colors("blue")
    end

    -- 4) Move: random-walk with obstacle avoidance, ignoring stop triggers.
    if turn_timer > 0 then
        -- Random turn in progress: spin in place briefly.
        robot.wheels.set_velocity(-MAX_VELOCITY/2, MAX_VELOCITY/2)
        turn_timer = turn_timer - 1
    else
        if math.random() < TURN_PROB then
            turn_timer = math.random(3, 8)
        else
            obstacle_avoidance_move()
        end
    end

    if tick_count % LOG_INTERVAL == 0 then
        local pos = robot.positioning.position
        -- DATA,<role>,<id>,<tick>,<x>,<y>,<stopped_near>,<issued_leave>
        log(string.format("DATA,A,%s,%d,%.3f,%.3f,%d,%d",
            robot.id, tick_count, pos.x, pos.y, stopped_near,
            issue_leave and 1 or 0))
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
    tick_count = 0
    turn_timer = 0
    robot.wheels.set_velocity(0, 0)
end

function destroy() end
