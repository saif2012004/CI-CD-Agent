"""
Test script for CI/CD Guardian Agent
Run this after installing dependencies: pip install -r requirements.txt
"""
import requests
import json
import time

BASE_URL = "http://localhost:8000"

def test_health():
    """Test the /health endpoint"""
    print("=" * 60)
    print("TEST 1: Health Check")
    print("=" * 60)
    try:
        response = requests.get(f"{BASE_URL}/health")
        print(f"Status Code: {response.status_code}")
        print(f"Response: {json.dumps(response.json(), indent=2)}")
        assert response.status_code == 200
        print("✅ Health check passed!\n")
        return True
    except Exception as e:
        print(f"❌ Health check failed: {e}\n")
        return False

def test_analyze_critical_failure():
    """Test pipeline analysis with critical failures"""
    print("=" * 60)
    print("TEST 2: Analyze Pipeline with Critical Failures")
    print("=" * 60)
    
    test_data = {
        "pipeline_id": "test-critical-123",
        "status": "failed",
        "duration_seconds": 450,
        "logs": "Build failed due to test failures",
        "vulnerabilities": ["CVE-2023-12345", "CVE-2023-54321"],
        "branch": "main",
        "commit_sha": "abc123def456",
        "test_coverage_percent": 65.0,
        "is_direct_push": True,
        "pr_approved": False,
        "pr_reviewers_count": 0
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/analyze",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        # Verify critical issues are detected
        assert response.status_code == 200
        assert result["severity"] == "critical"
        assert len(result["anomalies"]) > 0
        assert result["escalate_to_supervisor"] == True
        
        print("\n✅ Critical failure detection passed!")
        print(f"   - Detected {len(result['anomalies'])} anomalies")
        print(f"   - Severity: {result['severity']}")
        print(f"   - Escalate to supervisor: {result['escalate_to_supervisor']}\n")
        return True
    except Exception as e:
        print(f"❌ Critical failure test failed: {e}\n")
        return False

def test_analyze_success():
    """Test pipeline analysis with successful build"""
    print("=" * 60)
    print("TEST 3: Analyze Successful Pipeline")
    print("=" * 60)
    
    test_data = {
        "pipeline_id": "test-success-456",
        "status": "success",
        "duration_seconds": 180,
        "logs": "Build completed successfully",
        "vulnerabilities": [],
        "branch": "feature/test-branch",
        "commit_sha": "def456abc789",
        "test_coverage_percent": 95.0,
        "is_direct_push": False,
        "pr_approved": True,
        "pr_reviewers_count": 2
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/analyze",
            json=test_data,
            headers={"Content-Type": "application/json"}
        )
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        # Verify no critical issues
        assert response.status_code == 200
        assert len(result["anomalies"]) == 0
        
        print("\n✅ Successful pipeline test passed!")
        print(f"   - No anomalies detected")
        print(f"   - Severity: {result['severity']}\n")
        return True
    except Exception as e:
        print(f"❌ Success test failed: {e}\n")
        return False

def test_metrics():
    """Test the /metrics endpoint"""
    print("=" * 60)
    print("TEST 4: Get Metrics")
    print("=" * 60)
    try:
        response = requests.get(f"{BASE_URL}/metrics")
        print(f"Status Code: {response.status_code}")
        result = response.json()
        print(f"Response: {json.dumps(result, indent=2)}")
        
        assert response.status_code == 200
        assert "total_pipelines_analyzed" in result
        assert "success_rate_percent" in result
        
        print("\n✅ Metrics test passed!")
        print(f"   - Total pipelines: {result['total_pipelines_analyzed']}")
        print(f"   - Success rate: {result['success_rate_percent']}%\n")
        return True
    except Exception as e:
        print(f"❌ Metrics test failed: {e}\n")
        return False

def test_docs():
    """Test that API docs are accessible"""
    print("=" * 60)
    print("TEST 5: API Documentation")
    print("=" * 60)
    try:
        response = requests.get(f"{BASE_URL}/docs")
        print(f"Status Code: {response.status_code}")
        assert response.status_code == 200
        print("✅ API docs accessible at http://localhost:8000/docs\n")
        return True
    except Exception as e:
        print(f"❌ Docs test failed: {e}\n")
        return False

def run_all_tests():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("CI/CD GUARDIAN AGENT - TEST SUITE")
    print("=" * 60 + "\n")
    
    print("⏳ Waiting for server to start...")
    time.sleep(2)
    
    results = []
    results.append(("Health Check", test_health()))
    results.append(("Critical Failure Analysis", test_analyze_critical_failure()))
    results.append(("Success Analysis", test_analyze_success()))
    results.append(("Metrics", test_metrics()))
    results.append(("API Docs", test_docs()))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The agent is working correctly.")
        print("\n📝 Next steps for Render deployment:")
        print("   1. Push code to GitHub")
        print("   2. Connect GitHub repo to Render")
        print("   3. Render will auto-detect render.yaml")
        print("   4. Your agent will be live at: https://cicd-guardian-agent.onrender.com")
    else:
        print("\n⚠️  Some tests failed. Please review the errors above.")
    
    print("\n" + "=" * 60 + "\n")

if __name__ == "__main__":
    try:
        run_all_tests()
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed: {e}")

