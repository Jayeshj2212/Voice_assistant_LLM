from fastapi.testclient import TestClient

from app import app
from config import Settings

client = TestClient(app)


def test_default_tts_engine_uses_f5():
    settings = Settings()
    assert settings.tts_engine == 'f5'


def test_home_page_loads_and_shows_demo_metrics():
    response = client.get('/')
    assert response.status_code == 200
    assert 'AI Telecaller' in response.text
    assert 'Lead Pipeline' in response.text
    assert 'Conversion' in response.text


def test_call_page_renders_script():
    response = client.get('/call?language=hi&campaign=sales')
    assert response.status_code == 200
    assert 'AI Telecaller' in response.text
    assert 'sales' in response.text.lower()
    assert 'हिन्दी' in response.text


def test_generate_api_handles_lead_input():
    response = client.post(
        '/api/generate',
        json={
            'language': 'hi',
            'campaign': 'sales',
            'lead_name': 'Amit',
            'customer_input': 'Lead wants a discount and asks for a callback today.'
        }
    )
    assert response.status_code == 200
    payload = response.json()
    assert 'reply' in payload
    assert 'Amit' in payload['reply'] or 'sales' in payload['reply'].lower()


def test_dummy_call_endpoint_returns_conversation_flow():
    response = client.post(
        '/api/dummy-call',
        json={
            'language': 'hi',
            'campaign': 'loan',
            'lead_name': 'Amit',
            'duration_minutes': 2
        }
    )
    assert response.status_code == 200
    payload = response.json()
    assert 'conversation' in payload
    assert isinstance(payload['conversation'], list)
    assert len(payload['conversation']) >= 3
    assert payload['status'] == 'started'


def test_live_voice_turn_endpoint_accepts_audio_and_returns_reply():
    sample_wav = (
        b'RIFF' + b'\x00\x00\x00\x00' + b'WAVEfmt ' + b'\x10\x00\x00\x00' + b'\x01\x00\x01\x00'
        b'\x40\x1f\x00\x00' + b'\x80\x3e\x00\x00' + b'\x02\x00\x00\x00' + b'\x04\x00\x00\x00'
        b'\x00\x00\x00\x00' + b'data' + b'\x00\x00\x00\x00'
    )
    response = client.post(
        '/api/live-call/turn',
        files={'audio': ('voice.wav', sample_wav, 'audio/wav')},
        data={'language': 'hi', 'campaign': 'loan', 'lead_name': 'Amit'}
    )
    assert response.status_code == 200
    payload = response.json()
    assert 'transcript' in payload
    assert 'reply' in payload
    assert 'audio_url' in payload


def test_lead_sync_and_disposition_endpoints_work():
    sync_response = client.post('/api/lead-sync', json={
        'lead_id': 'demo-001',
        'name': 'Amit Sharma',
        'phone': '+91 98765 43210',
        'language': 'hi',
        'interest': 'home loan'
    })
    assert sync_response.status_code == 200
    assert 'status' in sync_response.json()

    disposition_response = client.post('/api/disposition', json={
        'lead_id': 'demo-001',
        'disposition': 'interested',
        'follow_up': 'Tomorrow 3 PM'
    })
    assert disposition_response.status_code == 200
    assert 'status' in disposition_response.json()


def test_voice_summary_endpoint_generates_summary():
    response = client.post('/api/voice-summary', json={
        'lead_name': 'Amit',
        'language': 'hi',
        'transcript': 'Customer says he is interested but wants pricing and callback tomorrow morning.'
    })
    assert response.status_code == 200
    payload = response.json()
    assert 'summary' in payload
    assert len(payload['summary']) > 0
