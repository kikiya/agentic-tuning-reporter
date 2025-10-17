#!/bin/bash

# Load Sample Data for Testing
# This creates a "bookly" database with 100,000 book records
# Use this to test the AI agent's report generation capabilities

echo "📚 Loading sample data for testing..."
echo ""

# Drop the bookly database if it exists
echo "1. Dropping existing bookly database (if any)..."
cockroach sql --insecure --execute="
DROP DATABASE IF EXISTS bookly CASCADE;"

# Create the bookly database
echo "2. Creating bookly database..."
cockroach sql --insecure --execute="
CREATE DATABASE bookly;"
echo "✅ Successfully created the bookly database."
echo ""

# Create the book table
echo "3. Creating book table..."
cockroach sql --insecure --execute="
CREATE TABLE bookly.book (
    book_id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    title STRING NOT NULL,
    author STRING NOT NULL,
    price FLOAT NOT NULL,
    format STRING NOT NULL,
    publish_date DATE NOT NULL
);"
echo "✅ Successfully created the book table"
echo ""

# Import 100000 rows of data into the book table
echo "4. Importing 100,000 rows of sample data..."
echo "   (This may take a minute...)"
cockroach sql --insecure --execute="
IMPORT INTO bookly.book (book_id, title, author, price, format, publish_date)
CSV DATA ('https://cockroach-university-public.s3.amazonaws.com/100000_books.csv')
WITH skip = '1';"

echo ""
echo "✅ Sample data loaded successfully!"
echo ""
echo "You can now test the AI agent with:"
echo "  - Database: bookly"
echo "  - App: bookly"
echo ""
echo "Try generating a report from the UI or with:"
echo "  curl -X POST \"http://localhost:8002/generate-report\" \\"
echo "    -H \"Content-Type: application/json\" \\"
echo "    -d '{\"database\": \"bookly\", \"app\": \"bookly\"}'"
echo ""
