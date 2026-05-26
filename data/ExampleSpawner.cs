// ExampleSpawner.cs
// Demonstrates a tiered dungeon spawner for the Isle of Dread.
// Level determines which creature set is active.

using System;
using Server;
using Server.Mobiles;

namespace ServUO.IsleOfDread
{
    public class IsleDreadSpawner : Item
    {
        private int m_Level;

        [CommandProperty(AccessLevel.GameMaster)]
        public int Level
        {
            get => m_Level;
            set
            {
                m_Level = Math.Clamp(value, 1, 12);
                InvalidateProperties();
            }
        }

        [Constructable]
        public IsleDreadSpawner() : base(0x1B7B)
        {
            Name    = "Isle of Dread Spawner";
            Movable = false;
            m_Level = 1;
        }

        public IsleDreadSpawner(Serial serial) : base(serial) { }

        // Called by a region heartbeat every 5 minutes.
        public void Tick()
        {
            switch (m_Level)
            {
                case int l when l >= 1 && l <= 3:
                    SpawnCreature<VoidWraith>();
                    break;

                case int l when l >= 4 && l <= 6:
                    SpawnCreature<VoidWraith>();
                    SpawnCreature<CorruptedSeaDrake>();
                    break;

                case int l when l >= 7 && l <= 11:
                    SpawnCreature<CorruptedSeaDrake>();
                    break;

                case 12:
                    SpawnBoss<Vorynthas>();
                    break;
            }
        }

        private void SpawnCreature<T>() where T : BaseCreature, new()
        {
            var mob = new T();
            mob.MoveToWorld(Location, Map);
        }

        private void SpawnBoss<T>() where T : BaseCreature, new()
        {
            // Bosses spawn only once until killed
            foreach (Mobile m in Map.GetMobilesInRange(Location, 20))
            {
                if (m is T)
                    return; // already alive
            }
            SpawnCreature<T>();
        }

        public override void Serialize(GenericWriter writer)
        {
            base.Serialize(writer);
            writer.Write(0); // version
            writer.Write(m_Level);
        }

        public override void Deserialize(GenericReader reader)
        {
            base.Deserialize(reader);
            int version = reader.ReadInt();
            m_Level = reader.ReadInt();
        }
    }
}
