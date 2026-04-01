#!/usr/bin/env bash
# Simulates the run-toolbelt skill running inside Claude Code

G='\033[0;32m'   # green
B='\033[0;34m'   # blue
Y='\033[1;33m'   # yellow
C='\033[0;36m'   # cyan
D='\033[2;37m'   # dim
W='\033[1;37m'   # bold white
NC='\033[0m'

printf "\n"
printf "${D}> /run-toolbelt document_url=https://docs.toolbelt.ai/intro.pdf question=\"What is Toolbelt?\"${NC}\n"
sleep 0.8

printf "\n"
printf "${C}● Phase 0  Verifying Toolbelt MCP connection...${NC}\n"
sleep 0.6
printf "${G}  ✓ Connected${NC}  |  namespace: demo-workspace  |  1 namespace found\n"
sleep 0.3

printf "\n"
printf "${C}● Phase 1  Resolving namespace...${NC}\n"
sleep 0.4
printf "${G}  ✓ Using${NC}  demo-workspace  (a3f2c1d9-4b2e-4a7c-9f1d-8e3b0c2d6a5f)\n"
sleep 0.2

printf "\n"
printf "${C}● Phase 2  Inspecting current state...${NC}\n"
sleep 0.5
printf "${G}  ✓ Context loaded${NC}  |  0 tables  |  0 vector collections\n"
sleep 0.2

printf "\n"
printf "${C}● Phase 3  Uploading document...${NC}\n"
sleep 0.4
printf "  ${D}file:${NC} intro.pdf  ${D}source:${NC} docs.toolbelt.ai\n"
sleep 0.8
printf "  ${Y}[ingest]${NC}   running...\n"
sleep 1.2
printf "  ${G}[ingest]${NC}   completed ✓\n"
sleep 0.4
printf "  ${Y}[semantic]${NC} running...\n"
sleep 1.6
printf "  ${G}[semantic]${NC} completed ✓\n"
sleep 0.3
printf "${G}  ✓ Ingested${NC}  →  table: ${W}intro_pdf${NC}\n"
sleep 0.3

printf "\n"
printf "${C}● Phase 5  Answering question...${NC}\n"
sleep 0.4
printf "  ${D}toolbelt_search  question=\"What is Toolbelt?\"${NC}\n"
sleep 1.2
printf "${G}  ✓ Done${NC}\n"

printf "\n"
printf "${W}RESULT:${NC}\n"
printf "  ${D}namespace_id:${NC}   a3f2c1d9-4b2e-4a7c-9f1d-8e3b0c2d6a5f\n"
printf "  ${D}phases_run:${NC}     [0, 1, 2, 3, 5]\n"
printf "  ${D}document_table:${NC} intro_pdf\n"
printf "  ${D}answer:${NC}         Toolbelt is a GPU-accelerated data workspace\n"
printf "                  providing SQL, vector search, knowledge graphs,\n"
printf "                  geospatial queries, and Kafka streaming via MCP.\n"
printf "  ${D}sources:${NC}        [intro.pdf]\n"
printf "\n"
