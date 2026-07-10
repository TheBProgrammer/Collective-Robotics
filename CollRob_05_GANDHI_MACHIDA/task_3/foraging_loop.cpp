/*
 * Tutorial 5 - Task 3: loop functions for the foraging experiment.
 *
 * Two jobs:
 *
 *   1) Measure swarm performance from ground truth. An object counts as
 *      collected once its centre enters the home zone (a disc of radius
 *      HOME_RADIUS around the home light). Counting from the simulator rather
 *      than from the robots' own reports avoids double counting, which the
 *      camera-based estimate is prone to.
 *
 *   2) Respawn every collected object at a random position in the foraging
 *      field. This keeps the number of objects constant, so the swarm never
 *      runs out of resource during the fixed observation period, and it stops
 *      delivered objects from piling up at the edge of the home zone (a pile
 *      would sit inside the robots' camera range and corrupt the bumper's
 *      object count).
 *
 * The collected total is printed at the end as   COLLECTED,<n>
 */

#include <argos3/core/simulator/loop_functions.h>
#include <argos3/core/simulator/simulator.h>
#include <argos3/core/simulator/entity/embodied_entity.h>
#include <argos3/core/utility/math/vector3.h>
#include <argos3/core/utility/math/quaternion.h>
#include <argos3/core/utility/math/rng.h>
#include <argos3/plugins/simulator/entities/cylinder_entity.h>

#include <iostream>

using namespace argos;

class CForagingLoopFunctions : public CLoopFunctions {

public:

   virtual void Init(TConfigurationNode& t_node) {
      Real fHomeX = -1.75, fHomeY = 0.0;
      GetNodeAttributeOrDefault(t_node, "home_x",      fHomeX,        fHomeX);
      GetNodeAttributeOrDefault(t_node, "home_y",      fHomeY,        fHomeY);
      m_cHome.Set(fHomeX, fHomeY, 0.0);
      GetNodeAttributeOrDefault(t_node, "home_radius", m_fHomeRadius, 0.70);
      GetNodeAttributeOrDefault(t_node, "field_min_x", m_fFieldMinX,  -0.40);
      GetNodeAttributeOrDefault(t_node, "field_max_x", m_fFieldMaxX,   1.75);
      GetNodeAttributeOrDefault(t_node, "field_min_y", m_fFieldMinY,  -1.75);
      GetNodeAttributeOrDefault(t_node, "field_max_y", m_fFieldMaxY,   1.75);
      m_pcRNG = CRandom::CreateRNG("argos");
      m_unCollected = 0;
   }

   virtual void Reset() {
      m_unCollected = 0;
   }

   /* After each physics step, harvest every object that reached home. */
   virtual void PostStep() {
      CSpace::TMapPerType* pcCylinders = NULL;
      try {
         pcCylinders = &GetSpace().GetEntitiesByType("cylinder");
      } catch(CARGoSException& ex) {
         return;   /* no cylinders in this experiment */
      }

      for(CSpace::TMapPerType::iterator it = pcCylinders->begin();
          it != pcCylinders->end(); ++it) {
         CCylinderEntity& cCyl = *any_cast<CCylinderEntity*>(it->second);
         const CVector3& cPos = cCyl.GetEmbodiedEntity().GetOriginAnchor().Position;

         Real fDist = Sqrt(Square(cPos.GetX() - m_cHome.GetX()) +
                           Square(cPos.GetY() - m_cHome.GetY()));
         if(fDist < m_fHomeRadius) {
            ++m_unCollected;
            MoveToField(cCyl);
         }
      }
   }

   virtual void Destroy() {
      LOG << "COLLECTED," << m_unCollected << std::endl;
      LOG.Flush();
   }

   UInt32 GetCollected() const { return m_unCollected; }

private:

   /* Teleport an object to a free random spot in the foraging field. */
   void MoveToField(CCylinderEntity& c_cyl) {
      for(UInt32 i = 0; i < 100; ++i) {
         CVector3 cPos(m_pcRNG->Uniform(CRange<Real>(m_fFieldMinX, m_fFieldMaxX)),
                       m_pcRNG->Uniform(CRange<Real>(m_fFieldMinY, m_fFieldMaxY)),
                       0.0);
         if(MoveEntity(c_cyl.GetEmbodiedEntity(), cPos, CQuaternion(), false)) {
            return;
         }
      }
      LOGERR << "[foraging_loop] could not respawn " << c_cyl.GetId() << std::endl;
   }

   CVector3   m_cHome;
   Real       m_fHomeRadius;
   Real       m_fFieldMinX, m_fFieldMaxX, m_fFieldMinY, m_fFieldMaxY;
   CRandom::CRNG* m_pcRNG;
   UInt32     m_unCollected;
};

REGISTER_LOOP_FUNCTIONS(CForagingLoopFunctions, "foraging_loop")
