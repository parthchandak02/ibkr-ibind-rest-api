#!/bin/bash
echo "Cleaning up development files..."
rm -f dev.py sample.txt positions.csv ibind_positions_test.py
rm -rf __pycache__ .history
find . -name ".DS_Store" -delete
echo "Done! Files cleaned up for production."
