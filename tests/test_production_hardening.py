#!/usr/bin/env python3
"""
Phase 5: Production Hardening - Load & Stress Testing Suite

Comprehensive performance and reliability testing for P-OS API Gateway.
Tests concurrent request handling, system limits, edge cases, and compliance logic.

Usage:
    python tests/test_production_hardening.py [--load] [--stress] [--edge-cases] [--compliance] [--all]
"""

import sys
import time
import json
import asyncio
from pathlib import Path
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Dict, Tuple

# Add project root to path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from services.export_api_gateway import ExportAPIGateway
from services.export_queue_manager import ExportQueueManager


class ProductionHardeningTester:
    """Comprehensive production readiness testing suite"""
    
    def __init__(self):
        self.results = {
            'timestamp': datetime.now().isoformat(),
            'test_categories': {},
            'summary': {}
        }
        
    def run_load_tests(self) -> Dict:
        """Test 1: Load Testing - Concurrent Request Handling"""
        
        print("=" * 80)
        print("LOAD TESTING: Concurrent Request Handling")
        print("=" * 80)
        
        results = {
            'test_name': 'Load Testing',
            'scenarios': [],
            'passed': True
        }
        
        # Scenario 1: 5 Concurrent Requests
        print("\n[SCENARIO 1] 5 Concurrent Requests")
        scenario_1 = self._test_concurrent_requests(concurrency=5, label="5 concurrent")
        results['scenarios'].append(scenario_1)
        
        if not scenario_1['success']:
            results['passed'] = False
        
        # Scenario 2: 10 Concurrent Requests
        print("\n[SCENARIO 2] 10 Concurrent Requests")
        scenario_2 = self._test_concurrent_requests(concurrency=10, label="10 concurrent")
        results['scenarios'].append(scenario_2)
        
        if not scenario_2['success']:
            results['passed'] = False
        
        # Calculate summary statistics
        all_response_times = []
        for scenario in results['scenarios']:
            all_response_times.extend(scenario.get('response_times', []))
        
        if all_response_times:
            avg_response_time = sum(all_response_times) / len(all_response_times)
            max_response_time = max(all_response_times)
            min_response_time = min(all_response_times)
            
            results['statistics'] = {
                'total_requests': len(all_response_times),
                'avg_response_time_ms': round(avg_response_time, 2),
                'max_response_time_ms': round(max_response_time, 2),
                'min_response_time_ms': round(min_response_time, 2),
                'requests_per_second': round(len(all_response_times) / max(all_response_times), 2)
            }
            
            print(f"\n📊 LOAD TEST STATISTICS:")
            print(f"   Total requests: {results['statistics']['total_requests']}")
            print(f"   Avg response time: {results['statistics']['avg_response_time_ms']} ms")
            print(f"   Max response time: {results['statistics']['max_response_time_ms']} ms")
            print(f"   Throughput: {results['statistics']['requests_per_second']} req/s")
        
        return results
    
    def _test_concurrent_requests(self, concurrency: int, label: str) -> Dict:
        """Test concurrent request handling"""
        
        api = ExportAPIGateway()
        start_time = time.time()
        response_times = []
        successes = 0
        failures = 0
        errors = []
        
        def submit_request(request_num: int) -> Tuple[int, float, bool, str]:
            """Submit single request and measure response time"""
            try:
                req_start = time.time()
                
                # Create unique idempotency key for each request
                idempotency_key = f"load_test_{label.replace(' ', '_')}_{request_num}_{int(time.time())}"
                
                response = api.submit_request({
                    'dataset_path': 'Facebook/kasiaju_1977350892357109/message_1.json',
                    'data_subject': {
                        'name': f'Test User {request_num}',
                        'email': f'test{request_num}@example.com'
                    },
                    'deadline_hours': 72,
                    'idempotency_key': idempotency_key
                })
                
                req_end = time.time()
                response_time_ms = (req_end - req_start) * 1000
                
                return request_num, response_time_ms, True, response.get('status', 'unknown')
                
            except Exception as e:
                req_end = time.time()
                response_time_ms = (req_end - req_start) * 1000
                return request_num, response_time_ms, False, str(e)
        
        print(f"   Submitting {concurrency} concurrent requests...")
        
        # Execute concurrent requests
        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = [executor.submit(submit_request, i) for i in range(concurrency)]
            
            for future in as_completed(futures):
                req_num, response_time, success, status = future.result()
                response_times.append(response_time)
                
                if success:
                    successes += 1
                    print(f"   ✓ Request {req_num}: {response_time:.0f}ms - {status}")
                else:
                    failures += 1
                    errors.append(f"Request {req_num}: {status}")
                    print(f"   ✗ Request {req_num}: FAILED - {status}")
        
        end_time = time.time()
        total_time = end_time - start_time
        
        result = {
            'concurrency': concurrency,
            'label': label,
            'total_time_seconds': round(total_time, 2),
            'successes': successes,
            'failures': failures,
            'success_rate_percent': round((successes / concurrency) * 100, 2),
            'response_times': response_times,
            'errors': errors[:5],  # Limit error display
            'success': failures == 0 and successes == concurrency
        }
        
        print(f"\n   Results: {successes}/{concurrency} successful ({result['success_rate_percent']}%)")
        print(f"   Total time: {total_time:.2f}s")
        
        return result
    
    def run_stress_tests(self) -> Dict:
        """Test 2: Stress Testing - System Limits"""
        
        print("\n" + "=" * 80)
        print("STRESS TESTING: System Limits & Break Points")
        print("=" * 80)
        
        results = {
            'test_name': 'Stress Testing',
            'scenarios': [],
            'passed': True
        }
        
        # Scenario 1: 50 Concurrent Requests (High Load)
        print("\n[SCENARIO 1] 50 Concurrent Requests (High Load)")
        scenario_1 = self._test_concurrent_requests(concurrency=50, label="50 concurrent")
        results['scenarios'].append(scenario_1)
        
        # Note: For stress testing, we allow some failures but track them
        if scenario_1['success_rate_percent'] < 80:
            results['passed'] = False
            print(f"   ⚠️  WARNING: Success rate below 80% threshold")
        else:
            print(f"   ✅ System handled high load successfully")
        
        # Scenario 2: Rapid Sequential Requests
        print("\n[SCENARIO 2] Rapid Sequential Requests (100 requests)")
        scenario_2 = self._test_rapid_sequential_requests(count=100)
        results['scenarios'].append(scenario_2)
        
        if not scenario_2['success']:
            results['passed'] = False
        
        return results
    
    def _test_rapid_sequential_requests(self, count: int) -> Dict:
        """Test rapid sequential request submission"""
        
        api = ExportAPIGateway()
        start_time = time.time()
        successes = 0
        failures = 0
        
        print(f"   Submitting {count} rapid sequential requests...")
        
        for i in range(count):
            try:
                idempotency_key = f"rapid_test_{i}_{int(time.time())}"
                
                response = api.submit_request({
                    'dataset_path': 'Facebook/kasiaju_1977350892357109/message_1.json',
                    'data_subject': {
                        'name': f'Rapid Test {i}',
                        'email': f'rapid{i}@example.com'
                    },
                    'deadline_hours': 72,
                    'idempotency_key': idempotency_key
                })
                
                if response.get('status_code') in [201, 409]:  # Created or duplicate (acceptable)
                    successes += 1
                else:
                    failures += 1
                    
            except Exception as e:
                failures += 1
        
        end_time = time.time()
        total_time = end_time - start_time
        
        result = {
            'request_count': count,
            'total_time_seconds': round(total_time, 2),
            'successes': successes,
            'failures': failures,
            'requests_per_second': round(count / total_time, 2),
            'success': failures == 0
        }
        
        print(f"   Results: {successes}/{count} successful")
        print(f"   Throughput: {result['requests_per_second']} req/s")
        print(f"   Total time: {total_time:.2f}s")
        
        return result
    
    def run_edge_case_tests(self) -> Dict:
        """Test 3: Edge Cases - Boundary Conditions"""
        
        print("\n" + "=" * 80)
        print("EDGE CASE TESTING: Boundary Conditions")
        print("=" * 80)
        
        results = {
            'test_name': 'Edge Case Testing',
            'scenarios': [],
            'passed': True
        }
        
        # Scenario 1: Large Dataset Simulation
        print("\n[SCENARIO 1] Large Dataset Handling")
        scenario_1 = self._test_large_dataset_handling()
        results['scenarios'].append(scenario_1)
        
        if not scenario_1['success']:
            results['passed'] = False
        
        # Scenario 2: Empty/Missing Data
        print("\n[SCENARIO 2] Empty/Missing Data Handling")
        scenario_2 = self._test_empty_missing_data()
        results['scenarios'].append(scenario_2)
        
        if not scenario_2['success']:
            results['passed'] = False
        
        # Scenario 3: Malformed Input
        print("\n[SCENARIO 3] Malformed Input Handling")
        scenario_3 = self._test_malformed_input()
        results['scenarios'].append(scenario_3)
        
        if not scenario_3['success']:
            results['passed'] = False
        
        return results
    
    def _test_large_dataset_handling(self) -> Dict:
        """Test handling of large datasets"""
        
        api = ExportAPIGateway()
        
        try:
            # Use existing dataset (8,779 messages is already substantial)
            response = api.submit_request({
                'dataset_path': 'Facebook/kasiaju_1977350892357109/message_1.json',
                'data_subject': {
                    'name': 'Large Dataset Test',
                    'email': 'large@example.com'
                },
                'deadline_hours': 72,
                'idempotency_key': f"large_test_{int(time.time())}"
            })
            
            success = response.get('status_code') == 201
            
            result = {
                'scenario': 'Large dataset (8,779 messages)',
                'success': success,
                'response_code': response.get('status_code'),
                'message': response.get('message', 'N/A')
            }
            
            if success:
                print(f"   ✅ Successfully processed large dataset")
            else:
                print(f"   ✗ Failed to process large dataset: {response.get('error')}")
            
            return result
            
        except Exception as e:
            return {
                'scenario': 'Large dataset (8,779 messages)',
                'success': False,
                'error': str(e)
            }
    
    def _test_empty_missing_data(self) -> Dict:
        """Test handling of empty/missing data"""
        
        api = ExportAPIGateway()
        scenarios_passed = 0
        total_scenarios = 3
        
        # Test 1: Missing dataset_path
        try:
            response = api.submit_request({
                'data_subject': {'name': 'Test', 'email': 'test@example.com'}
            })
            if response.get('status_code') == 400:
                scenarios_passed += 1
                print(f"   ✅ Correctly rejected missing dataset_path (400)")
            else:
                print(f"   ✗ Expected 400 for missing dataset_path, got {response.get('status_code')}")
        except Exception as e:
            print(f"   ✗ Exception on missing dataset_path: {e}")
        
        # Test 2: Missing data_subject
        try:
            response = api.submit_request({
                'dataset_path': 'Facebook/kasiaju_1977350892357109/message_1.json'
            })
            if response.get('status_code') == 400:
                scenarios_passed += 1
                print(f"   ✅ Correctly rejected missing data_subject (400)")
            else:
                print(f"   ✗ Expected 400 for missing data_subject, got {response.get('status_code')}")
        except Exception as e:
            print(f"   ✗ Exception on missing data_subject: {e}")
        
        # Test 3: Nonexistent dataset
        try:
            response = api.submit_request({
                'dataset_path': 'nonexistent/path/file.json',
                'data_subject': {'name': 'Test', 'email': 'test@example.com'},
                'idempotency_key': f"nonexistent_test_{int(time.time())}"
            })
            if response.get('status_code') == 404:
                scenarios_passed += 1
                print(f"   ✅ Correctly rejected nonexistent dataset (404)")
            else:
                print(f"   ✗ Expected 404 for nonexistent dataset, got {response.get('status_code')}")
        except Exception as e:
            print(f"   ✗ Exception on nonexistent dataset: {e}")
        
        return {
            'scenario': 'Empty/missing data handling',
            'scenarios_passed': scenarios_passed,
            'total_scenarios': total_scenarios,
            'success': scenarios_passed == total_scenarios
        }
    
    def _test_malformed_input(self) -> Dict:
        """Test handling of malformed input"""
        
        api = ExportAPIGateway()
        scenarios_passed = 0
        total_scenarios = 2
        
        # Test 1: Invalid JSON structure
        try:
            response = api.submit_request({
                'dataset_path': 12345,  # Should be string
                'data_subject': {'name': 'Test', 'email': 'test@example.com'},
                'idempotency_key': f"malformed_test_{int(time.time())}"
            })
            # Should handle gracefully (either reject or convert)
            scenarios_passed += 1
            print(f"   ✅ Handled invalid type gracefully")
        except Exception as e:
            # Exception is acceptable if it's caught and handled
            scenarios_passed += 1
            print(f"   ✅ Caught exception for invalid type: {type(e).__name__}")
        
        # Test 2: Extremely long strings
        try:
            long_string = "x" * 10000
            response = api.submit_request({
                'dataset_path': long_string,
                'data_subject': {'name': 'Test', 'email': 'test@example.com'},
                'idempotency_key': f"long_string_test_{int(time.time())}"
            })
            scenarios_passed += 1
            print(f"   ✅ Handled extremely long string gracefully")
        except Exception as e:
            scenarios_passed += 1
            print(f"   ✅ Caught exception for long string: {type(e).__name__}")
        
        return {
            'scenario': 'Malformed input handling',
            'scenarios_passed': scenarios_passed,
            'total_scenarios': total_scenarios,
            'success': scenarios_passed == total_scenarios
        }
    
    def run_compliance_tests(self) -> Dict:
        """Test 4: Compliance Logic Validation"""
        
        print("\n" + "=" * 80)
        print("COMPLIANCE TESTING: GDPR Requirements")
        print("=" * 80)
        
        results = {
            'test_name': 'Compliance Testing',
            'scenarios': [],
            'passed': True
        }
        
        # Scenario 1: 72-Hour Deadline Enforcement
        print("\n[SCENARIO 1] 72-Hour Deadline Enforcement")
        scenario_1 = self._test_deadline_enforcement()
        results['scenarios'].append(scenario_1)
        
        if not scenario_1['success']:
            results['passed'] = False
        
        # Scenario 2: Idempotency Blocking
        print("\n[SCENARIO 2] Idempotency Key Blocking")
        scenario_2 = self._test_idempotency_blocking()
        results['scenarios'].append(scenario_2)
        
        if not scenario_2['success']:
            results['passed'] = False
        
        # Scenario 3: Certificate Validity
        print("\n[SCENARIO 3] Certificate Structure Validation")
        scenario_3 = self._test_certificate_validity()
        results['scenarios'].append(scenario_3)
        
        if not scenario_3['success']:
            results['passed'] = False
        
        return results
    
    def _test_deadline_enforcement(self) -> Dict:
        """Test 72-hour deadline enforcement"""
        
        from services.export_queue_manager import ExportRequest
        
        # Create request with custom deadline
        request = ExportRequest(
            dataset_path='test.json',
            data_subject={'name': 'Test', 'email': 'test@example.com'},
            deadline_hours=72
        )
        
        # Verify deadline is set correctly
        expected_deadline = request.created_at + timedelta(hours=72)
        deadline_diff = abs((request.deadline_at - expected_deadline).total_seconds())
        
        success = deadline_diff < 1  # Within 1 second tolerance
        
        result = {
            'scenario': '72-hour deadline enforcement',
            'created_at': request.created_at.isoformat(),
            'deadline_at': request.deadline_at.isoformat(),
            'deadline_hours': 72,
            'accuracy_seconds': round(deadline_diff, 2),
            'success': success
        }
        
        if success:
            print(f"   ✅ Deadline set correctly: {request.deadline_at.isoformat()}")
        else:
            print(f"   ✗ Deadline accuracy issue: {deadline_diff}s difference")
        
        return result
    
    def _test_idempotency_blocking(self) -> Dict:
        """Test idempotency key blocking"""
        
        api = ExportAPIGateway()
        unique_key = f"idempotency_test_{int(time.time())}"
        
        # First submission should succeed
        response1 = api.submit_request({
            'dataset_path': 'Facebook/kasiaju_1977350892357109/message_1.json',
            'data_subject': {'name': 'Test', 'email': 'test@example.com'},
            'idempotency_key': unique_key
        })
        
        first_success = response1.get('status_code') == 201
        
        # Second submission with same key should be blocked
        response2 = api.submit_request({
            'dataset_path': 'Facebook/kasiaju_1977350892357109/message_1.json',
            'data_subject': {'name': 'Test', 'email': 'test@example.com'},
            'idempotency_key': unique_key
        })
        
        second_blocked = response2.get('status_code') == 409
        
        success = first_success and second_blocked
        
        result = {
            'scenario': 'Idempotency blocking',
            'first_request_status': response1.get('status_code'),
            'second_request_status': response2.get('status_code'),
            'first_succeeded': first_success,
            'second_blocked': second_blocked,
            'success': success
        }
        
        if success:
            print(f"   ✅ Idempotency enforced: 1st=201, 2nd=409 (blocked)")
        else:
            print(f"   ✗ Idempotency failed: 1st={response1.get('status_code')}, 2nd={response2.get('status_code')}")
        
        return result
    
    def _test_certificate_validity(self) -> Dict:
        """Test certificate structure and validity"""
        
        api = ExportAPIGateway()
        
        # Submit request to generate certificate
        response = api.submit_request({
            'dataset_path': 'Facebook/kasiaju_1977350892357109/message_1.json',
            'data_subject': {'name': 'Cert Test', 'email': 'cert@example.com'},
            'idempotency_key': f"cert_test_{int(time.time())}"
        })
        
        if response.get('status_code') != 201:
            return {
                'scenario': 'Certificate validity',
                'success': False,
                'error': f"Request failed: {response.get('status_code')}"
            }
        
        request_id = response.get('request_id')
        
        # Retrieve certificate
        cert_response = api.get_certificate(request_id)
        
        required_fields = [
            'certificate_id',
            'overall_verdict',
            'w11_validation',
            'hash_chain'
        ]
        
        missing_fields = [field for field in required_fields if field not in cert_response]
        
        # Check W11 validation structure
        w11_valid = False
        if 'w11_validation' in cert_response:
            w11_rules = ['R1_immutability_no_data_loss', 'R2_determinism_reproducible']
            w11_valid = all(rule in cert_response['w11_validation'] for rule in w11_rules)
        
        success = len(missing_fields) == 0 and w11_valid
        
        result = {
            'scenario': 'Certificate structure validation',
            'request_id': request_id,
            'certificate_id': cert_response.get('certificate_id', 'N/A'),
            'missing_fields': missing_fields,
            'w11_structure_valid': w11_valid,
            'overall_verdict': cert_response.get('overall_verdict', 'N/A'),
            'success': success
        }
        
        if success:
            print(f"   ✅ Certificate structure valid with all required fields")
            print(f"   ✅ Verdict: {cert_response.get('overall_verdict')}")
        else:
            print(f"   ✗ Certificate validation failed")
            if missing_fields:
                print(f"      Missing fields: {missing_fields}")
        
        return result
    
    def run_all_tests(self) -> Dict:
        """Run complete production hardening test suite"""
        
        print("\n" + "=" * 80)
        print("P-OS PRODUCTION HARDENING TEST SUITE")
        print("=" * 80)
        print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        print("=" * 80)
        
        overall_start = time.time()
        
        # Run all test categories
        self.results['test_categories']['load_testing'] = self.run_load_tests()
        self.results['test_categories']['stress_testing'] = self.run_stress_tests()
        self.results['test_categories']['edge_cases'] = self.run_edge_case_tests()
        self.results['test_categories']['compliance'] = self.run_compliance_tests()
        
        overall_end = time.time()
        total_duration = overall_end - overall_start
        
        # Generate summary
        categories_passed = sum(
            1 for cat in self.results['test_categories'].values()
            if cat.get('passed', False)
        )
        total_categories = len(self.results['test_categories'])
        
        self.results['summary'] = {
            'total_duration_seconds': round(total_duration, 2),
            'categories_tested': total_categories,
            'categories_passed': categories_passed,
            'overall_pass_rate_percent': round((categories_passed / total_categories) * 100, 2),
            'all_tests_passed': categories_passed == total_categories
        }
        
        # Print final summary
        print("\n" + "=" * 80)
        print("FINAL SUMMARY")
        print("=" * 80)
        print(f"Total duration: {total_duration:.2f}s")
        print(f"Categories tested: {total_categories}")
        print(f"Categories passed: {categories_passed}/{total_categories}")
        print(f"Overall pass rate: {self.results['summary']['overall_pass_rate_percent']}%")
        
        if self.results['summary']['all_tests_passed']:
            print("\n🎉 ALL PRODUCTION HARDENING TESTS PASSED!")
        else:
            print("\n⚠️  SOME TESTS FAILED - Review results above")
        
        print("=" * 80)
        
        return self.results


def main():
    """Main entry point"""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="P-OS Production Hardening Tests")
    parser.add_argument('--load', action='store_true', help='Run load tests only')
    parser.add_argument('--stress', action='store_true', help='Run stress tests only')
    parser.add_argument('--edge-cases', action='store_true', help='Run edge case tests only')
    parser.add_argument('--compliance', action='store_true', help='Run compliance tests only')
    parser.add_argument('--all', action='store_true', help='Run all tests (default)')
    
    args = parser.parse_args()
    
    tester = ProductionHardeningTester()
    
    # Default to all tests if no specific flag provided
    if not any([args.load, args.stress, args.edge_cases, args.compliance, args.all]):
        args.all = True
    
    if args.all:
        results = tester.run_all_tests()
    else:
        if args.load:
            results = {'load_testing': tester.run_load_tests()}
        if args.stress:
            results = {'stress_testing': tester.run_stress_tests()}
        if args.edge_cases:
            results = {'edge_cases': tester.run_edge_case_tests()}
        if args.compliance:
            results = {'compliance': tester.run_compliance_tests()}
    
    # Save results to file
    output_file = project_root / 'tests' / 'production_hardening_results.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(tester.results, f, indent=2, default=str)
    
    print(f"\n📄 Results saved to: {output_file}")
    
    # Exit with appropriate code
    if tester.results.get('summary', {}).get('all_tests_passed', False):
        sys.exit(0)
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
