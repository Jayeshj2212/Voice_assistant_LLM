import os
from pathlib import Path
from uuid import uuid4

import requests
from fastapi import FastAPI, File, Form, Request, UploadFile
from fastapi.responses import FileResponse, JSONResponse
from fastapi.templating import Jinja2Templates

from config import settings
from core.call_manager import CallManager
from lead_demo import get_demo_pipeline, sample_leads
from services.crm_service import CRMService
from services.ollama_service import OllamaService
from services.tts_service import TTSService
from services.whisper_service import WhisperService

app = FastAPI(title='AI Telecaller Demo')
templates = Jinja2Templates(directory='templates')
call_manager = CallManager(base_dir=settings.call_recordings_dir)
ollama_service = OllamaService(settings.ollama_url, settings.ollama_model)
crm_service = CRMService(settings.crm_api_url, settings.crm_api_key)
whisper_service = WhisperService(settings.whisper_model)
tts_service = TTSService(settings.tts_engine, settings.tts_voice)

LANGUAGE_TEXT = {
    'hi': {
        'label': 'हिन्दी',
        'greeting': 'नमस्कार, मैं आपका AI टेलीकॉलर हूँ।',
        'script': 'हिन्दी',
        'prompt': 'आप एक बिक्री टेलीकॉलर हैं। ग्राहक को नम्रता से परिचय दें, प्रोडक्ट का लाभ बताएं, और फिर फॉलोअप के लिए सही समय का सुझाव दें।',
        'call_style': 'आप एक प्रोफेशनल टेलीकॉलर हैं। ग्राहक को विनम्रता से नमस्कार कहें, समस्या को समझें, समाधान बताएं, और 1-2 सवालों में सही फॉलोअप का निर्णय लें।'
    },
    'en': {
        'label': 'English',
        'greeting': 'Hello, I am your AI telecaller.',
        'script': 'English',
        'prompt': 'You are a sales telecaller. Greet the customer professionally, explain the offer clearly, and propose the next step with confidence.',
        'call_style': 'You are a polished outbound sales agent speaking in a friendly phone-call style. Keep it natural, concise, and conversational. Ask one clear question, acknowledge their concern, and move to the next best action.'
    },
    'bn': {
        'label': 'বাংলা',
        'greeting': 'নমস্কার, আমি আপনার AI টেলিকॉलर।',
        'script': 'বাংলা',
        'prompt': 'আপনি একজন বিক্রয় টেলিকেলর। গ্রাহককে নম্র ভাষায় পরিচয় দিন, পণ্যের সুবিধা বলুন, এবং পরবর্তী পদক্ষেপের জন্য সময় ঠিক করুন।',
        'call_style': 'আপনি একজন বন্ধুত্বপূর্ণ ফোনে কথা বলার স্টাইলের বিক্রয় এজেন্ট। সংক্ষেপে, স্বাভাবিকভাবে কথা বলুন, অনুরোধটি বুঝে নিন, এবং পরবর্তী পদক্ষেপকে একক স্পষ্ট প্রশ্নের মাধ্যমে সাজিয়ে দিন।'
    }
}

OLLAMA_URL = os.getenv('OLLAMA_URL', 'http://localhost:11434')


def build_llm_prompt(language: str, campaign: str, customer_input: str, lead_name: str = 'Prospect') -> str:
    config = LANGUAGE_TEXT.get(language, LANGUAGE_TEXT['hi'])
    return (
        f"Lead name: {lead_name}\n"
        f"Language: {config['script']}\n"
        f"Campaign: {campaign}\n"
        f"Customer context: {customer_input}\n\n"
        f"{config['prompt']}\n"
        "Keep it short, persuasive, and natural. Mention the lead by name when relevant."
    )


def build_phone_call_prompt(language: str, campaign: str, customer_input: str, lead_name: str = 'Prospect', conversation_context: str = '') -> str:
    config = LANGUAGE_TEXT.get(language, LANGUAGE_TEXT['hi'])
    normalized = (customer_input or '').strip().replace('\n', ' ')
    if len(normalized) < 2:
        normalized = 'Customer has not responded clearly yet.'

    if language == 'hi':
        return (
            f"आप एक प्रोफेशनल भारतीय टेलीकॉलर हैं जो फोन पर ग्राहक से बात कर रहे हैं।\n"
            f"Lead name: {lead_name}\n"
            f"Campaign: {campaign}\n"
            f"Customer message: {normalized}\n"
            f"Recent context: {conversation_context or 'No previous context.'}\n\n"
            f"{config['call_style']}\n"
            "- उत्तर 2-4 वाक्यों में दें।\n"
            "- फोन-कॉल जैसा नरम, प्राकृतिक, और भरोसेमंद शैली में बोलें।\n"
            "- ग्राहक की समस्या को समझें और एक स्पष्ट अगला कदम सुझाएं।\n"
            "- कृपया टेम्पलेटेड या बहुत रूटीन जवाब न दें।"
        )
    if language == 'bn':
        return (
            f"আপনি একজন প্রফেশনাল ভারতীয় টেলিকেলর, ফোনে গ্রাহকের সঙ্গে কথা বলছেন।\n"
            f"Lead name: {lead_name}\n"
            f"Campaign: {campaign}\n"
            f"Customer message: {normalized}\n"
            f"Recent context: {conversation_context or 'No previous context.'}\n\n"
            f"{config['call_style']}\n"
            "- উত্তর 2-4 বাক্যে দিন।\n"
            "- ফোন-কলে স্বাভাবিক, আন্তরিক, আর আত্মবিশ্বাসী ভাষায় কথা বলুন।\n"
            "- গ্রাহকের উদ্বেগ বুঝুন এবং একটি স্পষ্ট পরবর্তী পদক্ষেপ দিন।\n"
            "- খুব টেমপ্লেটেড উত্তর দেবেন না।"
        )

    return (
        f"You are a professional outbound sales agent speaking on a live phone call.\n"
        f"Lead name: {lead_name}\n"
        f"Campaign: {campaign}\n"
        f"Customer message: {normalized}\n"
        f"Recent context: {conversation_context or 'No previous context.'}\n\n"
        f"{config['call_style']}\n"
        "- Keep the answer 2-4 sentences long.\n"
        "- Sound like a natural live call, not a chatbot template.\n"
        "- Acknowledge the concern, answer directly, and propose one clear next step.\n"
        "- Do not repeat generic script phrases."
    )


def generate_open_source_reply(language: str, campaign: str, customer_input: str, lead_name: str = 'Prospect', conversation_context: str = '') -> str:
    config = LANGUAGE_TEXT.get(language, LANGUAGE_TEXT['hi'])
    normalized = (customer_input or '').strip()
    cleaned = normalized.replace('\n', ' ').strip()
    if len(cleaned) < 2:
        cleaned = 'Customer has not responded clearly yet.'

    prompt = build_phone_call_prompt(language, campaign, cleaned, lead_name, conversation_context)

    payload = {
        'model': os.getenv('OLLAMA_MODEL', 'llama3.2'),
        'prompt': prompt,
        'stream': False,
        'options': {'temperature': 0.8}
    }

    try:
        response = requests.post(f'{OLLAMA_URL}/api/generate', json=payload, timeout=60)
        response.raise_for_status()
        data = response.json()
        if data.get('response'):
            generated = data['response'].strip()
            if generated:
                lower_generated = generated.lower()
                if lead_name.lower() not in lower_generated and lead_name.lower().replace(' ', '') not in lower_generated:
                    generated = f"{lead_name}, regarding your {campaign} requirement: " + generated
                return generated
    except requests.RequestException:
        pass

    if 'hello' in cleaned.lower() or 'namaste' in cleaned.lower():
        return (
            f"Hello {lead_name}, nice to hear from you. I’m here to help with the {campaign} requirement and I can guide you through the right option and next step."
        )

    if any(k in cleaned.lower() for k in ['price', 'pricing', 'cost', 'rate', 'budget']):
        return (
            f"{lead_name}, thanks for asking about pricing. I can explain the package clearly and help you choose the best option for your requirement. Would you like a quick summary of the pricing and the next step?"
        )

    return (
        f"I understand your requirement, {lead_name}. I can help with the right option, explain the benefits clearly, and suggest the next step in a simple way for the {campaign} requirement."
    )


def build_dummy_call_flow(language: str, campaign: str, lead_name: str = 'Amit', duration_minutes: int = 2):
    """Legacy demo-only script. The product behavior should use the dynamic LLM route below."""
    config = LANGUAGE_TEXT.get(language, LANGUAGE_TEXT['hi'])
    duration_minutes = max(1, min(int(duration_minutes), 5))

    conversation = [
        {
            'speaker': 'agent',
            'text': f"{config['greeting']} {lead_name}, I understand your requirement around the {campaign} offer. Could you share what you are looking for today?"
        },
        {
            'speaker': 'lead',
            'text': 'I want pricing and a quick callback.'
        },
        {
            'speaker': 'agent',
            'text': 'Thanks for sharing that. I can help with pricing, benefits, and the next steps. Let me guide you clearly and keep it simple.'
        }
    ]

    return {
        'status': 'started',
        'campaign': campaign,
        'language': language,
        'lead_name': lead_name,
        'duration_minutes': duration_minutes,
        'conversation': conversation,
        'summary': (
            f"The agent engaged the lead in a natural way, clarified the need around {campaign}, "
            "addressed pricing and follow-up interest, and moved the conversation toward a structured next step."
        )
    }


def _make_live_call_response(language: str, campaign: str, lead_name: str, transcript: str, audio_file_name: str | None = None, ref_audio: str | None = None, ref_text: str | None = None):
    if not transcript or transcript.strip() == '':
        transcript = 'Customer did not provide any speech input.'

    normalized_transcript = transcript.strip()
    if len(normalized_transcript) > 160:
        normalized_transcript = normalized_transcript[:160] + '...'

    conversation_key = lead_name.lower().strip() or 'default'
    history = ''
    if conversation_key in call_manager.sessions_by_lead:
        history = ' | '.join(call_manager.sessions_by_lead[conversation_key][-3:])

    reply = generate_open_source_reply(language, campaign, normalized_transcript, lead_name, history)
    audio_dir = Path(settings.call_recordings_dir) / 'live_turns'
    audio_dir.mkdir(parents=True, exist_ok=True)
    audio_name = audio_file_name or f"reply_{uuid4().hex}.wav"
    output_path = audio_dir / audio_name
    tts_service.synthesize(reply, str(output_path), ref_audio=ref_audio or settings.f5_ref_audio, ref_text=ref_text or settings.f5_ref_text)

    call_manager.sessions_by_lead.setdefault(conversation_key, []).append(normalized_transcript)
    return {
        'transcript': normalized_transcript,
        'reply': reply,
        'audio_url': f'/api/audio/{audio_name}'
    }


@app.get('/')
async def home(request: Request):
    return templates.TemplateResponse(
        request,
        'index.html',
        {
            'request': request,
            'languages': LANGUAGE_TEXT,
            'pipeline': get_demo_pipeline(),
            'leads': sample_leads(),
        }
    )


@app.get('/call')
async def call_page(request: Request, language: str = 'hi', campaign: str = 'sales'):
    config = LANGUAGE_TEXT.get(language, LANGUAGE_TEXT['hi'])
    return templates.TemplateResponse(
        request,
        'call.html',
        {
            'request': request,
            'language_label': config['label'],
            'language_name': config['script'],
            'campaign': campaign,
            'greeting': config['greeting'],
            'prompt': config['prompt'],
            'lead_name': 'Amit',
            'lead_phone': '+91 98765 43210',
            'lead_city': 'Delhi',
        },
    )


@app.post('/api/generate')
async def api_generate(request: Request):
    data = await request.json()
    language = data.get('language', 'hi')
    campaign = data.get('campaign', 'sales')
    lead_name = data.get('lead_name', 'Amit')
    customer_input = data.get('customer_input', 'Lead wants a callback today and asks for pricing details.')
    reply = generate_open_source_reply(language, campaign, customer_input, lead_name)
    return JSONResponse({'reply': reply})


@app.post('/api/dummy-call')
async def api_dummy_call(request: Request):
    data = await request.json()
    language = data.get('language', 'hi')
    campaign = data.get('campaign', 'sales')
    lead_name = data.get('lead_name', 'Amit')
    duration_minutes = data.get('duration_minutes', 2)
    flow = build_dummy_call_flow(language, campaign, lead_name, duration_minutes)
    return JSONResponse(flow)


@app.post('/api/live-call/turn')
async def api_live_call_turn(
    request: Request,
    audio: UploadFile = File(default=None),
    language: str = Form('hi'),
    campaign: str = Form('sales'),
    lead_name: str = Form('Amit'),
    ref_audio: str = Form(''),
    ref_text: str = Form(''),
):
    file_bytes = await audio.read() if audio is not None else b''
    audio_dir = Path(settings.call_recordings_dir) / 'live_turns'
    audio_dir.mkdir(parents=True, exist_ok=True)

    transcript = ''
    audio_output_name = f"reply_{uuid4().hex}.wav"
    if file_bytes:
        temp_path = audio_dir / f"input_{uuid4().hex}.wav"
        temp_path.write_bytes(file_bytes)
        try:
            transcript = whisper_service.transcribe_audio(str(temp_path))
        except Exception:
            transcript = ''
        if not transcript or transcript == 'Transcription unavailable: local Whisper model not installed.':
            transcript = 'Customer asked for pricing and callback details.'

    if not transcript:
        transcript = 'Customer asked for pricing and callback details.'

    custom_ref_audio = ref_audio.strip() or None
    custom_ref_text = ref_text.strip() or None

    try:
        payload = _make_live_call_response(language, campaign, lead_name, transcript, audio_output_name, custom_ref_audio, custom_ref_text)
    except Exception:
        payload = {
            'transcript': transcript,
            'reply': generate_open_source_reply(language, campaign, transcript, lead_name),
            'audio_url': ''
        }
    return JSONResponse(payload)


@app.get('/api/audio/{file_name}')
async def api_audio_file(file_name: str):
    audio_path = Path(settings.call_recordings_dir) / 'live_turns' / file_name
    if not audio_path.exists():
        return JSONResponse({'detail': 'Audio not found'}, status_code=404)
    return FileResponse(audio_path)


@app.post('/api/live-call/finalize')
async def api_live_call_finalize(request: Request):
    data = await request.json()
    transcript = data.get('transcript', '')
    lead_name = data.get('lead_name', 'Amit')
    disposition = data.get('disposition', 'interested')
    follow_up = data.get('follow_up', 'Tomorrow 3 PM')
    crm_result = crm_service.update_disposition(data.get('lead_id', 'demo-001'), disposition, follow_up)

    prompt = (
        f"Lead name: {lead_name}\n"
        f"Disposition: {disposition}\n"
        f"Follow up: {follow_up}\n"
        f"Transcript: {transcript}\n\n"
        "Summarize the call: key concern, interest level, objections, and next action in 4 bullet points."
    )
    summary = ollama_service.generate(prompt)
    return JSONResponse({'summary': summary, 'disposition': crm_result})


@app.post('/api/lead-sync')
async def api_lead_sync(request: Request):
    data = await request.json()
    result = crm_service.sync_lead(data)
    return JSONResponse(result)


@app.post('/api/disposition')
async def api_disposition(request: Request):
    data = await request.json()
    result = crm_service.update_disposition(
        data.get('lead_id', 'demo-001'),
        data.get('disposition', 'interested'),
        data.get('follow_up', 'Tomorrow 3PM')
    )
    return JSONResponse(result)


@app.post('/api/voice-summary')
async def api_voice_summary(request: Request):
    data = await request.json()
    transcript = data.get('transcript', 'No transcript available.')
    language = data.get('language', settings.default_language)
    lead_name = data.get('lead_name', 'Amit')
    prompt = (
        f"Lead name: {lead_name}\n"
        f"Language: {language}\n"
        f"Transcript: {transcript}\n\n"
        "Summarize this call in 4 bullet points: customer intent, objections, sentiment, and next action."
    )
    summary = ollama_service.generate(prompt)
    return JSONResponse({'summary': summary})


@app.post('/api/test-tts')
async def api_test_tts(request: Request):
    data = await request.json()
    text = data.get('text', 'Hello, this is your AI telecaller.')
    ref_audio = data.get('ref_audio') or settings.f5_ref_audio
    ref_text = data.get('ref_text') or settings.f5_ref_text
    output_dir = settings.call_recordings_dir
    os.makedirs(output_dir, exist_ok=True)
    file_name = f"demo_{len(os.listdir(output_dir)) if os.path.exists(output_dir) else 0}.wav"
    output_path = os.path.join(output_dir, file_name)
    generated = tts_service.synthesize(text, output_path, ref_audio=ref_audio, ref_text=ref_text)
    return JSONResponse({'output_path': generated, 'ref_audio': ref_audio, 'ref_text': ref_text})


if __name__ == '__main__':
    import uvicorn
    uvicorn.run('app:app', host=settings.host, port=settings.port, reload=settings.debug)
