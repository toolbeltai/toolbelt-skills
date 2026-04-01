#!/usr/bin/env bash
# Simulates the geo-analyst skill running inside Claude Code

G='\033[0;32m'   # green
B='\033[0;34m'   # blue
Y='\033[1;33m'   # yellow
C='\033[0;36m'   # cyan
D='\033[2;37m'   # dim
W='\033[1;37m'   # bold white
NC='\033[0m'

printf "\n"
printf "${D}> /geo-analyst${NC}\n"
sleep 0.8

printf "\n"
printf "${C}● Phase 0  Verifying Toolbelt MCP connection...${NC}\n"
sleep 0.6
printf "${G}  ✓ Connected${NC}  |  namespace: demo-workspace\n"
sleep 0.3

printf "\n"
printf "${C}● Phase 1  Resolving namespace...${NC}\n"
sleep 0.4
printf "${G}  ✓ Using${NC}  demo-workspace  (a3f2c1d9-4b2e-4a7c-9f1d-8e3b0c2d6a5f)\n"
sleep 0.2

printf "\n"
printf "${C}● Phase 2  Uploading Tampa Bay sensor data...${NC}\n"
sleep 0.4
printf "  ${D}10 sensors  |  columns: id, name, lat, lon${NC}\n"
sleep 0.8
printf "  ${Y}[ingest]${NC}   running...\n"
sleep 1.2
printf "  ${G}[ingest]${NC}   completed ✓\n"
sleep 0.3
printf "${G}  ✓ Sensor table:${NC}  ${W}sensor_locations${NC}  (10 rows)\n"
sleep 0.3

printf "\n"
printf "${C}● Phase 3  Running GPU geospatial queries...${NC}\n"
sleep 0.3

printf "\n"
printf "  ${B}Query 1${NC}  Pairwise Distance  ${D}ST_DISTANCE()${NC}\n"
sleep 1.0
printf "  ┌────────────┬────────────┬────────────┐\n"
printf "  │ sensor_a   │ sensor_b   │ distance_m │\n"
printf "  ├────────────┼────────────┼────────────┤\n"
printf "  │ Sensor A   │ Sensor B   │      2,847 │\n"
printf "  │ Sensor A   │ Sensor J   │      4,213 │\n"
printf "  │ Sensor B   │ Sensor J   │      5,091 │\n"
printf "  └────────────┴────────────┴────────────┘\n"
sleep 0.5

printf "\n"
printf "  ${B}Query 2${NC}  Point-in-Polygon  ${D}ST_CONTAINS()${NC}\n"
sleep 0.9
printf "  Zone: Downtown Tampa bounding polygon\n"
printf "  ${G}  2 sensors inside zone:${NC}  Sensor A, Sensor B\n"
sleep 0.5

printf "\n"
printf "  ${B}Query 3${NC}  Track Line  ${D}ST_MAKELINE()${NC}\n"
sleep 0.9
printf "  LINESTRING(-82.4572 27.9506, -82.4398 27.9659, ...)\n"
printf "  ${G}  Track complete:${NC}  10 points\n"

printf "\n"
printf "${W}RESULT:${NC}\n"
printf "  ${D}namespace_id:${NC}    a3f2c1d9-4b2e-4a7c-9f1d-8e3b0c2d6a5f\n"
printf "  ${D}sensor_table:${NC}    sensor_locations  (10 rows)\n"
printf "  ${D}phases_run:${NC}      [0, 1, 2, 3]\n"
printf "\n"
printf "  ${D}distance_query:${NC}\n"
printf "    ${D}closest_pair:${NC}  Sensor A → Sensor B\n"
printf "    ${D}min_distance:${NC}  2,847 m\n"
printf "\n"
printf "  ${D}point_in_polygon:${NC}\n"
printf "    ${D}in_zone_count:${NC}   2\n"
printf "    ${D}in_zone_sensors:${NC} [Sensor A, Sensor B]\n"
printf "\n"
printf "  ${D}track:${NC}\n"
printf "    ${D}point_count:${NC}  10\n"
printf "\n"
