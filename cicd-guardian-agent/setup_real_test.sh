#!/bin/bash
# Quick setup script for testing Guardian Agent with a real repository

echo "🚀 CI/CD Guardian Agent - Real Repository Test Setup"
echo "====================================================="
echo ""

# Check if agent is running
echo "1️⃣ Checking if Guardian Agent is running..."
if curl -s http://localhost:8000/health > /dev/null 2>&1; then
    echo "   ✅ Agent is running at http://localhost:8000"
else
    echo "   ❌ Agent is not running!"
    echo "   Please start it first:"
    echo "   python -m uvicorn src.agent:app --port 8000"
    echo ""
    read -p "Press Enter to exit..."
    exit 1
fi

echo ""
echo "2️⃣ Choose testing method:"
echo "   a) Local testing with ngrok (temporary URL)"
echo "   b) Use deployed Render URL (permanent)"
echo "   c) Test with curl only (no GitHub integration)"
echo ""
read -p "Enter choice (a/b/c): " choice

case $choice in
    a)
        echo ""
        echo "📡 Setting up ngrok..."
        echo "ℹ️  You need ngrok installed: https://ngrok.com/download"
        echo ""
        read -p "Press Enter to continue once ngrok is installed..."
        
        echo ""
        echo "Starting ngrok tunnel..."
        echo "Run this in a new terminal:"
        echo ""
        echo "  ngrok http 8000"
        echo ""
        echo "Then copy the HTTPS URL (e.g., https://abc123.ngrok-free.app)"
        read -p "Enter your ngrok URL: " ngrok_url
        
        AGENT_URL="$ngrok_url"
        ;;
    b)
        echo ""
        read -p "Enter your Render URL (e.g., https://cicd-guardian-agent.onrender.com): " render_url
        AGENT_URL="$render_url"
        ;;
    c)
        echo ""
        echo "🧪 Testing with curl..."
        echo ""
        echo "Test 1: Health Check"
        curl http://localhost:8000/health
        echo ""
        echo ""
        
        echo "Test 2: Analyze Critical Failure"
        curl -X POST http://localhost:8000/analyze \
          -H "Content-Type: application/json" \
          -d '{
            "pipeline_id": "manual-test-123",
            "status": "failed",
            "duration_seconds": 300,
            "logs": "Manual test",
            "vulnerabilities": ["CVE-2023-12345"],
            "branch": "main",
            "commit_sha": "abc123",
            "test_coverage_percent": 65.0,
            "is_direct_push": true,
            "pr_approved": false,
            "pr_reviewers_count": 0
          }'
        echo ""
        echo ""
        
        echo "Test 3: Check Metrics"
        curl http://localhost:8000/metrics
        echo ""
        echo ""
        
        echo "✅ Manual curl testing complete!"
        echo "Visit http://localhost:8000/docs for interactive testing"
        exit 0
        ;;
    *)
        echo "Invalid choice"
        exit 1
        ;;
esac

echo ""
echo "3️⃣ GitHub Repository Setup"
echo ""
echo "To integrate with GitHub Actions:"
echo ""
echo "Step 1: Go to your test repository on GitHub"
echo ""
echo "Step 2: Add this file: .github/workflows/guardian-test.yml"
echo "        (File already created in this project)"
echo ""
echo "Step 3: Add GitHub Secret:"
echo "        Repository → Settings → Secrets → Actions"
echo "        Name: GUARDIAN_AGENT_URL"
echo "        Value: $AGENT_URL"
echo ""
echo "Step 4: Make a test commit:"
echo ""
echo "        git add .github/workflows/guardian-test.yml"
echo "        git commit -m 'Add Guardian Agent'"
echo "        git push origin main"
echo ""
echo "Step 5: Watch the results:"
echo "        - GitHub Actions tab (workflow run)"
echo "        - Your agent terminal (incoming requests)"
echo "        - Metrics: $AGENT_URL/metrics"
echo ""
echo "📚 For detailed instructions, see:"
echo "   - REAL_REPO_TESTING.md"
echo "   - QUICK_REAL_TEST.md"
echo ""
echo "✅ Setup complete!"
echo ""

