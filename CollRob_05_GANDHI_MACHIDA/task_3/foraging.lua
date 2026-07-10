-- Tutorial 5 - Task 3: foraging controller.
--
-- The robot searches the arena for objects (blue-LED cylinders), pushes them
-- to the home zone (marked by a bright yellow light), releases them, and goes
-- back out. Sensors used:
--
--   * footbot_proximity  (24 rays)  -- obstacles, and the bumper (see below)
--   * footbot_light      (24 rays)  -- phototaxis towards home, home detection
--   * omnidirectional camera        -- blue blobs = objects, yellow = home light
--   * range_and_bearing             -- tells "another robot" apart from "a wall"
--
-- ARGoS has no force/bumper sensor, so the bumper of the task sheet is
-- emulated: the bumper is *pressed* when the front proximity ring reports
-- contact AND the camera sees at least one object blob inside the front arc at
-- contact range. The measured *force* is the number of such blobs, i.e. how
-- many objects the robot is currently pushing.
--
-- Each cycle the controller reports the six values required by the sheet:
--   wheel velocities, error, collision, arena boundary, transporting, home zone.
-- The three-valued flags are 1 (true), 0 (false) and -1 (unknown).

------------------------------------------------------------------ parameters
local MAX_VELOCITY   = 15.0   -- cm/s
local TURN_GAIN      = 8.0

-- Proximity/camera geometry, measured on this ARGoS build. An object straight
-- ahead reads: 16.5 cm -> prox 1.00 (touching), 19 cm -> 0.37, 25 cm -> 0.11,
-- 35 cm -> 0.00. So the ring still fires well before the robot is in contact.
local PROX_THRESH    = 0.10   -- something is there
local BUMP_THRESH    = 0.35   -- the bumper is actually pressed (<= ~19 cm)
local PUSH_CM        = 18.5   -- blob distance counted as "being pushed"
local SENSE_CM       = 30.0   -- a blob this close can explain a proximity hit
local FRONT_ARC      = 0.7    -- rad, half-width of the pushing arc
local BEARING_TOL    = 0.7    -- rad, matching a proximity hit to a blob/neighbour
local RAB_NEAR_CM    = 25.0   -- a neighbour this close explains a proximity hit

-- Light-sum thresholds, calibrated against distance from the home light:
--   0.20 m -> 4.45   0.35 m -> 4.21   0.45 m -> 4.02   0.50 m -> 3.92
--   0.55 m -> 3.81   0.65 m -> 3.61   0.70 m -> 3.51   1.00 m -> 2.93
--
-- An object is collected once its centre is within 0.35 m of the light (see
-- home_radius in task3.argos). The robot pushing it is then ~0.52 m out
-- (sum ~3.88) and keeps driving towards the light for a moment afterwards, so
-- NEAR_HOME can sit tighter than that: it fires at ~0.47 m, which keeps the
-- robot from claiming a delivery when it merely loses an object near the nest.
local HOME_LIGHT     = 4.21   -- robot itself inside the home zone (0.35 m)
local NEAR_HOME      = 3.80   -- ~0.56 m: an object lost here crossed into home
local NO_COLLECT     = 3.61   -- do not pick objects up within 0.65 m of home

local LOST_TICKS     = 20     -- ticks without contact before we give up pushing
local SEEK_TICKS     = 40     -- ticks without seeing the target before re-searching
local BACKUP_TICKS   = 12     -- ticks of reversing after a delivery
local TURN_TICKS     = 14     -- ticks of turning after backing up
local STUCK_WIN      = 30     -- window (ticks) for the stuck/error detector
local STUCK_EPS      = 2.0    -- cm of travel below which we call it stuck
local ESCAPE_TICKS   = 10     -- ticks of being stuck before abandoning the object

local LOG_INTERVAL   = 10     -- ticks between DATA lines

local UNKNOWN, FALSE, TRUE = -1, 0, 1

------------------------------------------------------------------ state
local state, timer, seek_timer, lost_timer, tick
local delivered                 -- objects this robot has delivered
local hist_x, hist_y, hist_n    -- ring buffer for the stuck detector
local stuck_ticks               -- consecutive ticks with the error flag raised
local prev_force                -- bumper force on the previous cycle

function init()
   robot.colored_blob_omnidirectional_camera.enable()
   reset()
end

------------------------------------------------------------------ helpers
local function light_sum()
   local s = 0.0
   for i = 1, #robot.light do s = s + robot.light[i].value end
   return s
end

--- Vector sum of the light readings; points towards the light source.
local function light_vector()
   local x, y = 0.0, 0.0
   for i = 1, #robot.light do
      local v, a = robot.light[i].value, robot.light[i].angle
      x = x + v * math.cos(a)
      y = y + v * math.sin(a)
   end
   return x, y
end

--- Strongest proximity reading and its bearing.
local function max_proximity()
   local best, bearing = 0.0, 0.0
   for i = 1, #robot.proximity do
      if robot.proximity[i].value > best then
         best = robot.proximity[i].value
         bearing = robot.proximity[i].angle
      end
   end
   return best, bearing
end

--- Repulsion vector away from every obstacle seen by the proximity ring.
-- When `skip_front` is true the readings inside the pushing arc are ignored,
-- so a robot that is transporting does not steer away from its own object.
local function avoid_vector(skip_front)
   local x, y = 0.0, 0.0
   for i = 1, #robot.proximity do
      local v, a = robot.proximity[i].value, robot.proximity[i].angle
      if not (skip_front and math.abs(a) <= FRONT_ARC) then
         x = x - v * math.cos(a)
         y = y - v * math.sin(a)
      end
   end
   return x, y
end

--- Objects carry a pure blue LED. No robot state uses blue, so a blue blob is
-- always an object and never a team-mate.
local function is_object(blob)
   return blob.color.blue > 200 and blob.color.red < 100 and blob.color.green < 100
end

local function angle_diff(a, b)
   local d = (a - b) % (2 * math.pi)
   if d > math.pi then d = d - 2 * math.pi end
   return math.abs(d)
end

--- Nearest object blob anywhere in camera range, or nil.
local function nearest_object()
   local cam = robot.colored_blob_omnidirectional_camera
   local best = nil
   for i = 1, #cam do
      if is_object(cam[i]) and (best == nil or cam[i].distance < best.distance) then
         best = cam[i]
      end
   end
   return best
end

--- How many objects sit in the front arc at contact range: the bumper "force".
local function pushing_force()
   local cam = robot.colored_blob_omnidirectional_camera
   local n = 0
   for i = 1, #cam do
      if is_object(cam[i]) and cam[i].distance <= PUSH_CM
         and math.abs(cam[i].angle) <= FRONT_ARC then
         n = n + 1
      end
   end
   return n
end

--- Steer so that the robot heads along the vector (x, y) given in its own frame.
local function steer_towards(x, y, speed)
   local heading = math.atan2(y, x)
   local lv = speed - TURN_GAIN * heading
   local rv = speed + TURN_GAIN * heading
   lv = math.max(-MAX_VELOCITY, math.min(MAX_VELOCITY, lv))
   rv = math.max(-MAX_VELOCITY, math.min(MAX_VELOCITY, rv))
   robot.wheels.set_velocity(lv, rv)
   return lv, rv
end

--- Wander forward, turning away from obstacles.
local function wander()
   local ax, ay = avoid_vector()
   if math.sqrt(ax * ax + ay * ay) < 0.05 then
      -- free space: go straight, with an occasional random turn
      if math.random() < 0.03 then
         local turn = (math.random() - 0.5) * 2 * MAX_VELOCITY
         robot.wheels.set_velocity(MAX_VELOCITY - turn, MAX_VELOCITY + turn)
         return MAX_VELOCITY - turn, MAX_VELOCITY + turn
      end
      robot.wheels.set_velocity(MAX_VELOCITY, MAX_VELOCITY)
      return MAX_VELOCITY, MAX_VELOCITY
   end
   return steer_towards(ax, ay, MAX_VELOCITY * 0.6)
end

------------------------------------------------------------------ the six outputs
--- Classify the strongest proximity hit into collision / boundary.
-- A hit explained by a range-and-bearing neighbour is another robot (collision);
-- a hit explained by an object blob is the bumper, not an obstacle; anything
-- else that is close enough is the arena boundary.
local function classify_contact(force)
   local hit, bearing = max_proximity()
   if hit < PROX_THRESH then
      return FALSE, FALSE          -- collision, boundary
   end

   -- Two candidate explanations for the hit, each at some distance. A robot and
   -- an object can both lie near the same bearing, so believe the nearer one.
   local robot_d = math.huge
   for i = 1, #robot.range_and_bearing do
      local m = robot.range_and_bearing[i]
      if m.range < RAB_NEAR_CM
         and angle_diff(m.horizontal_bearing, bearing) < BEARING_TOL
         and m.range < robot_d then
         robot_d = m.range
      end
   end

   -- SENSE_CM, not PUSH_CM: the proximity ring still fires at 25 cm, so an
   -- object that is merely close (not yet touched) must still explain the hit.
   local object_d = math.huge
   local cam = robot.colored_blob_omnidirectional_camera
   for i = 1, #cam do
      if is_object(cam[i]) and cam[i].distance <= SENSE_CM
         and angle_diff(cam[i].angle, bearing) < BEARING_TOL
         and cam[i].distance < object_d then
         object_d = cam[i].distance
      end
   end

   if robot_d == math.huge and object_d == math.huge then
      return FALSE, TRUE           -- nothing else explains it: a wall
   end
   if robot_d < object_d then
      return TRUE, FALSE           -- a neighbouring robot
   end
   return FALSE, FALSE             -- an object, not an obstacle
end

--- Stuck detector: commanded to move but the robot has not travelled.
local function error_flag(lv, rv)
   local p = robot.positioning.position
   hist_n = hist_n + 1
   local slot = (hist_n % STUCK_WIN) + 1
   local old_x, old_y = hist_x[slot], hist_y[slot]
   hist_x[slot], hist_y[slot] = p.x, p.y

   if hist_n < STUCK_WIN or old_x == nil then
      return UNKNOWN               -- not enough history yet
   end
   local commanded = math.abs(lv) + math.abs(rv)
   if commanded < 1.0 then
      return FALSE                 -- deliberately not moving
   end
   local travelled = math.sqrt((p.x - old_x)^2 + (p.y - old_y)^2) * 100.0
   if travelled < STUCK_EPS then return TRUE end
   return FALSE
end

------------------------------------------------------------------ main loop
function step()
   tick = tick + 1
   robot.range_and_bearing.set_data(1, 1)   -- "I am a robot"

   local lsum = light_sum()
   local at_home = lsum > HOME_LIGHT
   local force = pushing_force()
   local hit = select(1, max_proximity())
   local bumper = (hit > BUMP_THRESH) and force > 0

   local lv, rv = 0, 0
   local transporting = FALSE

   -- A robot that pushes its object into a wall off to the side of the nest
   -- would push forever: the object never enters the home zone, so contact is
   -- never lost. The error flag detects it; abandon the object and move on.
   if stuck_ticks > ESCAPE_TICKS and (state == "TRANSPORT" or state == "APPROACH") then
      state, timer = "BACKUP", BACKUP_TICKS
      stuck_ticks = 0
   end

   ---------------------------------------------------------------- SEARCH
   if state == "SEARCH" then
      robot.leds.set_all_colors("green")
      if at_home then
         -- inside home: walk away from the light, ignore the deposited objects
         local gx, gy = light_vector()
         lv, rv = steer_towards(-gx, -gy, MAX_VELOCITY)
      else
         local target = nearest_object()
         if target ~= nil and lsum < NO_COLLECT then
            state, seek_timer = "APPROACH", 0
            lv, rv = steer_towards(math.cos(target.angle), math.sin(target.angle),
                                   MAX_VELOCITY * 0.8)
         else
            lv, rv = wander()
         end
      end

   ---------------------------------------------------------------- APPROACH
   elseif state == "APPROACH" then
      robot.leds.set_all_colors("cyan")
      seek_timer = seek_timer + 1
      local target = nearest_object()

      if at_home or lsum >= NO_COLLECT then
         state = "SEARCH"                     -- do not harvest near the nest
         lv, rv = wander()
      elseif bumper then
         state, lost_timer = "TRANSPORT", 0   -- contact: start pushing
         lv, rv = steer_towards(1, 0, MAX_VELOCITY)
      elseif target == nil or seek_timer > SEEK_TICKS then
         state = "SEARCH"
         lv, rv = wander()
      else
         -- Head for the object. Obstacle repulsion may deflect us, but the
         -- target itself must not: once it is close, ignore the front sensors.
         local closing = target.distance <= SENSE_CM
         local ax, ay = avoid_vector(closing)
         local amag = math.sqrt(ax * ax + ay * ay)
         local tx, ty = math.cos(target.angle), math.sin(target.angle)
         if amag > 0.35 and not closing then
            lv, rv = steer_towards(ax, ay, MAX_VELOCITY * 0.6)
         else
            lv, rv = steer_towards(tx, ty, MAX_VELOCITY * 0.8)
         end
      end

   ---------------------------------------------------------------- TRANSPORT
   elseif state == "TRANSPORT" then
      robot.leds.set_all_colors("red")
      transporting = TRUE

      -- Decide on the *falling edge* of contact: the tick the object leaves the
      -- bumper is the only moment that carries information about where it went.
      -- Waiting any longer lets the robot coast towards the light and then
      -- claim a delivery for an object it merely dropped on the way.
      if force == 0 and prev_force > 0 and lsum > NEAR_HOME then
         -- Contact lost right at the nest: the object crossed into the home
         -- zone and was collected. (The simulator removes it there, which is
         -- exactly what a deposit looks like to the robot.)
         delivered = delivered + 1
         log(string.format("DELIVER,%s,%d,1", robot.id, tick))
         state, timer = "BACKUP", BACKUP_TICKS
         transporting = FALSE
         robot.wheels.set_velocity(-MAX_VELOCITY, -MAX_VELOCITY)
         lv, rv = -MAX_VELOCITY, -MAX_VELOCITY
      else
         if force == 0 then
            lost_timer = lost_timer + 1
            if lost_timer > LOST_TICKS then   -- object slipped away
               state = "SEARCH"
               transporting = FALSE
               lv, rv = wander()
            end
         else
            lost_timer = 0
         end

         if state == "TRANSPORT" then
            -- Push towards the light. The repulsion vector skips the pushing
            -- arc, so walls and team-mates still deflect us but the object we
            -- are pushing does not.
            local gx, gy = light_vector()
            local gmag = math.sqrt(gx * gx + gy * gy)
            gx, gy = gx / gmag, gy / gmag
            local ax, ay = avoid_vector(true)
            lv, rv = steer_towards(gx + ax, gy + ay, MAX_VELOCITY)
         end
      end

   ---------------------------------------------------------------- BACKUP
   elseif state == "BACKUP" then
      robot.leds.set_all_colors("magenta")
      robot.wheels.set_velocity(-MAX_VELOCITY, -MAX_VELOCITY)
      lv, rv = -MAX_VELOCITY, -MAX_VELOCITY
      timer = timer - 1
      if timer <= 0 then state, timer = "TURN", TURN_TICKS end

   ---------------------------------------------------------------- TURN
   elseif state == "TURN" then
      robot.leds.set_all_colors("magenta")
      robot.wheels.set_velocity(MAX_VELOCITY, -MAX_VELOCITY)
      lv, rv = MAX_VELOCITY, -MAX_VELOCITY
      timer = timer - 1
      if timer <= 0 then state = "SEARCH" end
   end

   ---------------------------------------------------------------- reporting
   local collision, boundary = classify_contact(force)
   local err = error_flag(lv, rv)
   local home = at_home and TRUE or FALSE

   stuck_ticks = (err == TRUE) and (stuck_ticks + 1) or 0
   prev_force = force

   if tick % LOG_INTERVAL == 0 then
      local p = robot.positioning.position
      -- DATA,<id>,<tick>,<vl>,<vr>,<err>,<collision>,<boundary>,<transporting>,
      --      <home>,<force>,<delivered>,<state>,<x>,<y>
      log(string.format("DATA,%s,%d,%.2f,%.2f,%d,%d,%d,%d,%d,%d,%d,%s,%.2f,%.2f",
          robot.id, tick, lv, rv, err, collision, boundary,
          transporting, home, force, delivered, state, p.x, p.y))
   end
end

function reset()
   state, timer, seek_timer, lost_timer, tick = "SEARCH", 0, 0, 0, 0
   delivered = 0
   hist_x, hist_y, hist_n = {}, {}, 0
   stuck_ticks, prev_force = 0, 0
   robot.wheels.set_velocity(0, 0)
end

function destroy()
   log(string.format("TOTAL,%s,%d", robot.id, delivered))
end
