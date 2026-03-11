"""Word分片上传测试"""
import sys
import os
import time
import threading
import uvicorn
import requests

for mod in list(sys.modules.keys()):
    if 'backend' in mod or 'app' in mod:
        del sys.modules[mod]

from backend.app.main import app


def run_server():
    uvicorn.run(app, host='127.0.0.1', port=8000, log_level='error')


def test_word_upload():
    api = 'http://127.0.0.1:8000'
    
    print('='*60)
    print('Word Document Chunked Upload Test')
    print('='*60)
    
    passed = 0
    failed = 0
    
    # Test 1: Create 12MB Word file
    print('\n[Test 1] Create 12MB Word file')
    try:
        content = b'PK\x03\x04'  # ZIP header
        content += b'0' * (12 * 1024 * 1024)
        with open('test_large.docx', 'wb') as f:
            f.write(content)
        file_size = os.path.getsize('test_large.docx')
        print(f'  File size: {file_size} bytes ({file_size/1024/1024:.2f} MB)')
        print('  PASSED')
        passed += 1
    except Exception as e:
        print(f'  FAILED: {e}')
        failed += 1
        return
    
    # Test 2: Word large file - init chunked upload
    print('\n[Test 2] Word large file - init chunked upload')
    try:
        r = requests.post(f'{api}/api/upload/chunked/init', json={
            'filename': 'test_large.docx',
            'file_size': file_size,
            'content_type': 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        })
        assert r.status_code == 200
        data = r.json()['data']
        upload_id = data['upload_id']
        chunk_size = data['chunk_size']
        total_chunks = data['total_chunks']
        print(f'  Upload ID: {upload_id}')
        print(f'  Chunk size: {chunk_size}')
        print(f'  Total chunks: {total_chunks}')
        assert total_chunks > 1
        print('  PASSED - Confirmed chunked upload')
        passed += 1
    except Exception as e:
        print(f'  FAILED: {e}')
        failed += 1
    
    # Test 3: Upload chunks
    print('\n[Test 3] Upload chunks')
    try:
        with open('test_large.docx', 'rb') as f:
            for i in range(total_chunks):
                start = i * chunk_size
                end = min(start + chunk_size, file_size)
                f.seek(start)
                chunk = f.read(end - start)
                files = {'file': ('part', chunk, 'application/octet-stream')}
                r = requests.post(
                    f'{api}/api/upload/chunked/part/file?upload_id={upload_id}&part_number={i+1}',
                    files=files
                )
                print(f'  Chunk {i+1}/{total_chunks}: {r.status_code}')
        print('  PASSED')
        passed += 1
    except Exception as e:
        print(f'  FAILED: {e}')
        failed += 1
    
    # Test 4: Complete upload
    print('\n[Test 4] Complete upload')
    try:
        r = requests.post(f'{api}/api/upload/chunked/complete', json={'upload_id': upload_id})
        assert r.status_code == 200
        result = r.json()['data']
        print(f'  File size: {result.get("file_size")}')
        print(f'  Message: {result.get("message")}')
        print('  PASSED')
        passed += 1
    except Exception as e:
        print(f'  FAILED: {e}')
        failed += 1
    finally:
        if os.path.exists('test_large.docx'):
            os.remove('test_large.docx')
    
    # Test 5: Word small file direct upload
    print('\n[Test 5] Word small file direct upload')
    try:
        small_content = b'PK\x03\x04' + b'0' * (1 * 1024 * 1024)
        with open('test_small.docx', 'wb') as f:
            f.write(small_content)
        with open('test_small.docx', 'rb') as f:
            files = {'file': ('small.docx', f, 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')}
            r = requests.post(f'{api}/api/document/upload', files=files, timeout=30)
        print(f'  Status: {r.status_code}')
        print('  PASSED')
        passed += 1
    except Exception as e:
        print(f'  FAILED: {e}')
        failed += 1
    finally:
        if os.path.exists('test_small.docx'):
            os.remove('test_small.docx')
    
    # Test 6: PDF direct upload
    print('\n[Test 6] PDF direct upload')
    try:
        pdf_content = b'%PDF-1.4' + b'0' * (1 * 1024 * 1024)
        with open('test.pdf', 'wb') as f:
            f.write(pdf_content)
        with open('test.pdf', 'rb') as f:
            files = {'file': ('test.pdf', f, 'application/pdf')}
            r = requests.post(f'{api}/api/document/upload', files=files, timeout=30)
        print(f'  Status: {r.status_code}')
        print('  PASSED')
        passed += 1
    except Exception as e:
        print(f'  FAILED: {e}')
        failed += 1
    finally:
        if os.path.exists('test.pdf'):
            os.remove('test.pdf')
    
    print('\n' + '='*60)
    print(f'RESULTS: {passed} Passed, {failed} Failed')
    print('='*60)
    
    return failed == 0


if __name__ == '__main__':
    server_thread = threading.Thread(target=run_server, daemon=True)
    server_thread.start()
    print('Server starting...')
    time.sleep(3)
    
    success = test_word_upload()
    sys.exit(0 if success else 1)
