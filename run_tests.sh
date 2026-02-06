#!/bin/bash
# Quick Test Runner Script for Duobingo API Tests
# Usage: ./run_tests.sh [option]

set -e

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== Duobingo API Test Suite ===${NC}\n"

case "${1:-all}" in
  all)
    echo -e "${GREEN}Running all tests...${NC}"
    pytest tests/ -v
    ;;
  
  coverage)
    echo -e "${GREEN}Running tests with coverage report...${NC}"
    pytest tests/ --cov=app --cov-report=html --cov-report=term
    echo -e "\n${GREEN}Coverage report generated in htmlcov/index.html${NC}"
    ;;
  
  auth)
    echo -e "${GREEN}Running authentication tests...${NC}"
    pytest tests/test_auth.py -v
    ;;
  
  classrooms)
    echo -e "${GREEN}Running classroom tests...${NC}"
    pytest tests/test_classrooms.py -v
    ;;
  
  modules)
    echo -e "${GREEN}Running module tests...${NC}"
    pytest tests/test_modules.py -v
    ;;
  
  quizzes)
    echo -e "${GREEN}Running quiz tests...${NC}"
    pytest tests/test_quizzes.py -v
    ;;
  
  questions)
    echo -e "${GREEN}Running question tests...${NC}"
    pytest tests/test_questions.py -v
    ;;
  
  sessions)
    echo -e "${GREEN}Running session/gameplay tests...${NC}"
    pytest tests/test_sessions.py -v
    ;;
  
  leitner)
    echo -e "${GREEN}Running Leitner system tests...${NC}"
    pytest tests/test_leitner.py -v
    ;;
  
  stats)
    echo -e "${GREEN}Running statistics tests...${NC}"
    pytest tests/test_stats.py -v
    ;;
  
  media)
    echo -e "${GREEN}Running media tests...${NC}"
    pytest tests/test_media.py -v
    ;;
  
  quick)
    echo -e "${GREEN}Running quick smoke tests (fail fast)...${NC}"
    pytest tests/ -x --maxfail=3
    ;;
  
  failed)
    echo -e "${GREEN}Re-running failed tests from last run...${NC}"
    pytest tests/ --lf -v
    ;;
  
  *)
    echo "Usage: $0 {all|coverage|auth|classrooms|modules|quizzes|questions|sessions|leitner|stats|media|quick|failed}"
    echo ""
    echo "Options:"
    echo "  all         - Run all tests (default)"
    echo "  coverage    - Run with coverage report"
    echo "  auth        - Run authentication tests only"
    echo "  classrooms  - Run classroom management tests"
    echo "  modules     - Run module management tests"
    echo "  quizzes     - Run quiz management tests"
    echo "  questions   - Run question bank tests"
    echo "  sessions    - Run quiz session/gameplay tests"
    echo "  leitner     - Run Leitner spaced repetition tests"
    echo "  stats       - Run statistics and progression tests"
    echo "  media       - Run media upload tests"
    echo "  quick       - Quick smoke test (fail fast)"
    echo "  failed      - Re-run only failed tests"
    exit 1
    ;;
esac

echo -e "\n${GREEN}Tests completed!${NC}"
