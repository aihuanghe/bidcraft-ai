"""回归测试脚本"""
import sys
import os
import time
import threading
import uvicorn
import requests

# 清理模块缓存
for mod in list(sys.modules.keys()):
    if 'backend' in mod or 'app' in mod:
        del sys.modules[mod]

from backend.app.main import app


def run_server():
    uvicorn.run(app, host='127.0.0.1', port=8000, log_level='error')


def test_all():
    """运行所有测试"""
    print('=' * 60)
    print('BidCraft AI Regression Tests')
    print('=' * 60)
    
    api = 'http://127.0.0.1:8000'
    passed = 0
    failed = 0
    
    # Test 1: Health Check
    print('\n[Test 1] Health Check')
    try:
        r = requests.get(f'{api}/health', timeout=5)
        assert r.status_code == 200
        print(f'  Status: {r.status_code}')
        print(f'  Response: {r.json()}')
        print('  PASSED')
        passed += 1
    except Exception as e:
        print(f'  FAILED: {e}')
        failed += 1
    
    # Test 2: Config Save (Original API)
    print('\n[Test 2] Config Save (Original API)')
    try:
        r = requests.post(f'{api}/api/config/save', json={
            'api_key': 'test-key-123',
            'model_name': 'gpt-3.5-turbo'
        }, timeout=5)
        assert r.status_code == 200
        print(f'  Status: {r.status_code}')
        print(f'  Response: {r.json()}')
        print('  PASSED')
        passed += 1
    except Exception as e:
        print(f'  FAILED: {e}')
        failed += 1
    
    # Test 3: Config Load (Original API)
    print('\n[Test 3] Config Load (Original API)')
    try:
        r = requests.get(f'{api}/api/config/load', timeout=5)
        assert r.status_code == 200
        data = r.json()
        print(f'  Status: {r.status_code}')
        print(f'  API Key: {data.get("api_key")}')
        print('  PASSED')
        passed += 1
    except Exception as e:
        print(f'  FAILED: {e}')
        failed += 1
    
    # Test 4: File Upload (Original API)
    print('\n[Test 4] File Upload (Original API)')
    try:
        with open('test_small.txt', 'w') as f:
            f.write('test content')
        with open('test_small.txt', 'rb') as f:
            r = requests.post(f'{api}/api/document/upload', 
                            files={'file': ('test.txt', f, 'text/plain')}, timeout=10)
        os.remove('test_small.txt')
        print(f'  Status: {r.status_code}')
        print('  PASSED (original API responds)')
        passed += 1
    except Exception as e:
        print(f'  FAILED: {e}')
        failed += 1
    
    # Test 5: Create Project (New API)
    print('\n[Test 5] Create Project (New API)')
    try:
        r = requests.post(f'{api}/api/projects/', json={
            'name': 'Test Project',
            'budget': 100000,
            'tender_company': 'Test Company'
        }, timeout=5)
        assert r.status_code == 200
        data = r.json()
        project_id = data.get('id')
        print(f'  Status: {r.status_code}')
        print(f'  Project ID: {project_id}')
        print('  PASSED')
        passed += 1
    except Exception as e:
        print(f'  FAILED: {e}')
        failed += 1
        project_id = None
    
    # Test 6: Get Project List
    print('\n[Test 6] Get Project List')
    try:
        r = requests.get(f'{api}/api/projects/', timeout=5)
        assert r.status_code == 200
        data = r.json()
        print(f'  Status: {r.status_code}')
        print(f'  Count: {len(data)}')
        print('  PASSED')
        passed += 1
    except Exception as e:
        print(f'  FAILED: {e}')
        failed += 1
    
    # Test 7: Get Single Project
    print('\n[Test 7] Get Single Project')
    try:
        r = requests.get(f'{api}/api/projects/{project_id}', timeout=5)
        assert r.status_code == 200
        data = r.json()
        print(f'  Status: {r.status_code}')
        print(f'  Name: {data.get("name")}')
        print('  PASSED')
        passed += 1
    except Exception as e:
        print(f'  FAILED: {e}')
        failed += 1
    
    # Test 8: Update Project
    print('\n[Test 8] Update Project')
    try:
        r = requests.put(f'{api}/api/projects/{project_id}', json={
            'status': 'in_progress',
            'progress': 50
        }, timeout=5)
        assert r.status_code == 200
        data = r.json()
        print(f'  Status: {r.status_code}')
        print(f'  Status: {data.get("status")}')
        print(f'  Progress: {data.get("progress")}')
        print('  PASSED')
        passed += 1
    except Exception as e:
        print(f'  FAILED: {e}')
        failed += 1
    
    # Test 9: Create Material
    print('\n[Test 9] Create Material (New API)')
    try:
        r = requests.post(f'{api}/api/materials/', json={
            'material_type': 'business_license',
            'name': 'Business License',
            'bid_project_id': project_id
        }, timeout=5)
        assert r.status_code == 200
        data = r.json()
        material_id = data.get('id')
        print(f'  Status: {r.status_code}')
        print(f'  Material ID: {material_id}')
        print('  PASSED')
        passed += 1
    except Exception as e:
        print(f'  FAILED: {e}')
        failed += 1
        material_id = None
    
    # Test 10: Get Material List
    print('\n[Test 10] Get Material List')
    try:
        r = requests.get(f'{api}/api/materials/', timeout=5)
        assert r.status_code == 200
        data = r.json()
        print(f'  Status: {r.status_code}')
        print(f'  Count: {len(data)}')
        print('  PASSED')
        passed += 1
    except Exception as e:
        print(f'  FAILED: {e}')
        failed += 1
    
    # Test 11: Chunked Upload Init
    print('\n[Test 11] Chunked Upload Init (New API)')
    try:
        r = requests.post(f'{api}/api/upload/chunked/init', json={
            'filename': 'test.pdf',
            'file_size': 15000000,
            'content_type': 'application/pdf'
        }, timeout=5)
        assert r.status_code == 200
        data = r.json()['data']
        upload_id = data.get('upload_id')
        print(f'  Status: {r.status_code}')
        print(f'  Upload ID: {upload_id}')
        print(f'  Total Chunks: {data.get("total_chunks")}')
        print('  PASSED')
        passed += 1
    except Exception as e:
        print(f'  FAILED: {e}')
        failed += 1
        upload_id = None
    
    # Test 12: Chunked Upload Status
    print('\n[Test 12] Chunked Upload Status')
    try:
        r = requests.get(f'{api}/api/upload/chunked/status/{upload_id}', timeout=5)
        assert r.status_code == 200
        data = r.json()['data']
        print(f'  Status: {r.status_code}')
        print(f'  Upload Status: {data.get("status")}')
        print('  PASSED')
        passed += 1
    except Exception as e:
        print(f'  FAILED: {e}')
        failed += 1
    
    # Test 13: Chunked Upload Cancel
    print('\n[Test 13] Chunked Upload Cancel')
    try:
        r = requests.delete(f'{api}/api/upload/chunked/{upload_id}', timeout=5)
        assert r.status_code == 200
        print(f'  Status: {r.status_code}')
        print('  PASSED')
        passed += 1
    except Exception as e:
        print(f'  FAILED: {e}')
        failed += 1
    
    # Test 14: Delete Project
    print('\n[Test 14] Delete Project')
    try:
        r = requests.delete(f'{api}/api/projects/{project_id}', timeout=5)
        assert r.status_code == 200
        print(f'  Status: {r.status_code}')
        print('  PASSED')
        passed += 1
    except Exception as e:
        print(f'  FAILED: {e}')
        failed += 1
    
    # Test 15: Delete Material
    print('\n[Test 15] Delete Material')
    try:
        r = requests.delete(f'{api}/api/materials/{material_id}', timeout=5)
        assert r.status_code == 200
        print(f'  Status: {r.status_code}')
        print('  PASSED')
        passed += 1
    except Exception as e:
        print(f'  FAILED: {e}')
        failed += 1
    
    # Test 16: Full Chunked Upload (12MB)
    print('\n[Test 16] Full Chunked Upload (12MB)')
    try:
        # Create 12MB test file
        with open('test_large.dat', 'wb') as f:
            f.write(b'0' * (12 * 1024 * 1024))
        file_size = os.path.getsize('test_large.dat')
        
        # Init
        r = requests.post(f'{api}/api/upload/chunked/init', json={
            'filename': 'test_large.dat',
            'file_size': file_size,
            'content_type': 'application/octet-stream'
        }, timeout=5)
        upload_id = r.json()['data']['upload_id']
        chunk_size = r.json()['data']['chunk_size']
        total_chunks = r.json()['data']['total_chunks']
        
        # Upload chunks
        with open('test_large.dat', 'rb') as f:
            for i in range(total_chunks):
                start = i * chunk_size
                end = min(start + chunk_size, file_size)
                f.seek(start)
                chunk = f.read(end - start)
                files = {'file': ('part', chunk, 'application/octet-stream')}
                r = requests.post(
                    f'{api}/api/upload/chunked/part/file?upload_id={upload_id}&part_number={i+1}',
                    files=files, timeout=30
                )
                print(f'  Chunk {i+1}/{total_chunks}: {r.status_code}')
        
        # Complete
        r = requests.post(f'{api}/api/upload/chunked/complete', 
                         json={'upload_id': upload_id}, timeout=30)
        result = r.json()['data']
        print(f'  Status: {r.status_code}')
        print(f'  File Size: {result.get("file_size")}')
        print(f'  MD5: {result.get("file_hash")}')
        
        os.remove('test_large.dat')
        print('  PASSED')
        passed += 1
    except Exception as e:
        print(f'  FAILED: {e}')
        if os.path.exists('test_large.dat'):
            os.remove('test_large.dat')
        failed += 1
    
    # Summary
    print('\n' + '=' * 60)
    print(f'RESULTS: {passed} Passed, {failed} Failed')
    print('=' * 60)
    
    if failed == 0:
        print('ALL TESTS PASSED!')
    else:
        print(f'{failed} test(s) failed.')
    
    return failed == 0


if __name__ == '__main__':
    # Start server
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    print('Server starting...')
    time.sleep(3)
    
    # Run tests
    success = test_all()
    sys.exit(0 if success else 1)
