import requests
import sys
from datetime import datetime
import json

class MediaPlayerAPITester:
    def __init__(self, base_url="https://audio-hub-583.preview.emergentagent.com"):
        self.base_url = base_url
        self.api_url = f"{base_url}/api"
        self.tests_run = 0
        self.tests_passed = 0
        self.test_results = []

    def run_test(self, name, method, endpoint, expected_status, data=None, timeout=10):
        """Run a single API test"""
        url = f"{self.api_url}/{endpoint}" if endpoint else self.api_url
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=timeout)

            success = response.status_code == expected_status
            result = {
                "test_name": name,
                "method": method,
                "endpoint": endpoint,
                "expected_status": expected_status,
                "actual_status": response.status_code,
                "success": success,
                "response_data": None,
                "error": None
            }

            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    result["response_data"] = response.json()
                except:
                    result["response_data"] = response.text
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                print(f"   Response: {response.text[:200]}...")
                result["error"] = response.text

            self.test_results.append(result)
            return success, response.json() if success and response.content else {}

        except requests.exceptions.Timeout:
            error_msg = f"Request timeout after {timeout} seconds"
            print(f"❌ Failed - {error_msg}")
            self.test_results.append({
                "test_name": name,
                "method": method,
                "endpoint": endpoint,
                "expected_status": expected_status,
                "actual_status": None,
                "success": False,
                "response_data": None,
                "error": error_msg
            })
            return False, {}
        except Exception as e:
            error_msg = f"Error: {str(e)}"
            print(f"❌ Failed - {error_msg}")
            self.test_results.append({
                "test_name": name,
                "method": method,
                "endpoint": endpoint,
                "expected_status": expected_status,
                "actual_status": None,
                "success": False,
                "response_data": None,
                "error": error_msg
            })
            return False, {}

    def test_api_root(self):
        """Test API root endpoint"""
        success, response = self.run_test(
            "API Root",
            "GET",
            "",
            200
        )
        return success

    def test_media_endpoint(self):
        """Test media files endpoint - should fetch from GitHub"""
        success, response = self.run_test(
            "Media Files from GitHub",
            "GET",
            "media",
            200,
            timeout=15  # GitHub API might be slower
        )
        
        if success:
            files = response.get('files', [])
            total = response.get('total', 0)
            repo = response.get('repo', '')
            
            print(f"   Found {total} media files from repo: {repo}")
            print(f"   Expected 8 songs, got: {total}")
            
            if total == 8:
                print("✅ Correct number of songs found")
            else:
                print(f"⚠️  Expected 8 songs but found {total}")
            
            # Check if files have required fields
            for i, file in enumerate(files[:3]):  # Check first 3 files
                required_fields = ['id', 'name', 'display_name', 'url', 'type']
                missing_fields = [field for field in required_fields if field not in file]
                if missing_fields:
                    print(f"⚠️  File {i+1} missing fields: {missing_fields}")
                else:
                    print(f"✅ File {i+1} has all required fields")
        
        return success, response

    def test_play_recording(self, file_name):
        """Test play recording endpoint"""
        success, response = self.run_test(
            f"Record Play for {file_name}",
            "POST",
            f"play/{file_name}",
            200
        )
        return success

    def test_stats_endpoint(self):
        """Test stats endpoint"""
        success, response = self.run_test(
            "Play Statistics",
            "GET",
            "stats",
            200
        )
        return success

def main():
    print("🎵 Starting Bestelerim Media Player API Tests")
    print("=" * 50)
    
    # Setup
    tester = MediaPlayerAPITester()
    
    # Test API root
    tester.test_api_root()
    
    # Test media endpoint (main functionality)
    media_success, media_response = tester.test_media_endpoint()
    
    # Test play recording if we have media files
    if media_success and media_response.get('files'):
        first_file = media_response['files'][0]
        tester.test_play_recording(first_file['name'])
    
    # Test stats endpoint
    tester.test_stats_endpoint()
    
    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print("❌ Some tests failed")
        
        # Print failed tests
        failed_tests = [test for test in tester.test_results if not test['success']]
        print(f"\n❌ Failed Tests ({len(failed_tests)}):")
        for test in failed_tests:
            print(f"   - {test['test_name']}: {test.get('error', 'Status code mismatch')}")
        
        return 1

if __name__ == "__main__":
    sys.exit(main())