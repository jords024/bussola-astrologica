import asyncio
import json
from pathlib import Path
import edge_tts

VOICE = "pt-BR-AntonioNeural" # Warm, clear, natural Brazilian Portuguese male voice
RATE = "-1%" # Natural speaking pace

SCRIPT_SEGMENTS = [
    # Cena 1: O Problema Real / Abertura (0 a ~14s)
    {"scene": 0, "text": "Sabe aquela sensação de acordar na segunda-feira sem saber onde colocar a sua energia?"},
    {"scene": 0, "text": "Ou passar semanas insistindo em coisas que simplesmente não andam?"},
    {"scene": 0, "text": "Foi exatamente para acabar com essa dúvida que criamos a Bússola."},

    # Cena 2: As Três Forças / Mapa Simples (14s a ~28s)
    {"scene": 1, "text": "Aqui dentro, nada de termos difíceis ou astrologia confusa."},
    {"scene": 1, "text": "Logo de cara, você vê suas três forças essenciais: seu Sol, sua Lua e seu Ascendente."},
    {"scene": 1, "text": "Tudo explicado de forma prática, direto ao ponto, com foco na sua vida real."},

    # Cena 3: O Mais Forte de Hoje / Porta Aberta (28s a ~44s)
    {"scene": 2, "text": "Mas o grande diferencial está aqui: O Mais Forte de Hoje."},
    {"scene": 2, "text": "O céu se move todos os dias."},
    {"scene": 2, "text": "A ferramenta cruza os planetas de agora com a sua data de nascimento."},
    {"scene": 2, "text": "Para te responder uma pergunta: qual porta está aberta para você avançar nesta semana?"},

    # Cena 4: Ação Prática / Direcionamento (44s a ~60s)
    {"scene": 3, "text": "Em vez de previsões vagas de jornal, você recebe um plano de ação claro."},
    {"scene": 3, "text": "Onde acelerar no trabalho, onde segurar a ansiedade, e onde os seus resultados fluem com naturalidade."},

    # Cena 5: Encerramento / 2 Minutos por Dia (60s a ~75s)
    {"scene": 4, "text": "Basta abrir o painel por dois minutos logo pela manhã."},
    {"scene": 4, "text": "Você para de remar contra a maré e ganha a clareza de quem sabe exatamente o próximo passo."},
    {"scene": 4, "text": "Bem-vindo à sua Bússola Astrológica."}
]

async def generate():
    audio_path = Path("video-studio/public/tour-narration.mp3")
    subs_path = Path("video-studio/src/tour-captions.json")
    
    full_text = " ".join(seg["text"] for seg in SCRIPT_SEGMENTS)
    
    communicate = edge_tts.Communicate(full_text, VOICE, rate=RATE)
    
    boundaries = []
    
    with open(audio_path, "wb") as file:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                file.write(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                start_sec = round(chunk["offset"] / 10_000_000, 3)
                end_sec = round((chunk["offset"] + chunk["duration"]) / 10_000_000, 3)
                text = chunk["text"].strip()
                boundaries.append({
                    "start": start_sec,
                    "end": end_sec,
                    "text": text
                })
                
    # Now match boundaries with scenes
    captions = []
    seg_idx = 0
    total_segs = len(SCRIPT_SEGMENTS)
    
    for b in boundaries:
        # Match text with SCRIPT_SEGMENTS
        matched_scene = 0
        if seg_idx < total_segs:
            matched_scene = SCRIPT_SEGMENTS[seg_idx]["scene"]
            seg_idx += 1
        captions.append({
            "start": b["start"],
            "end": b["end"],
            "text": b["text"],
            "scene": matched_scene
        })
        
    # Calculate scene boundaries from captions
    scene_starts = {}
    for c in captions:
        sc = c["scene"]
        if sc not in scene_starts:
            scene_starts[sc] = c["start"]
            
    # Total duration
    total_duration = captions[-1]["end"] + 2.5 if captions else 60.0
    
    result = {
        "audio": "tour-narration.mp3",
        "duration": total_duration,
        "totalFrames": int(total_duration * 30),
        "sceneStarts": scene_starts,
        "captions": captions
    }
    
    with open(subs_path, "w", encoding="utf-8") as f:
        json.dump(result, f, indent=2, ensure_ascii=False)
        
    print(f"Generated {audio_path} and {subs_path}")
    print(f"Total duration: {total_duration:.2f}s ({result['totalFrames']} frames)")
    print(f"Scenes: {scene_starts}")

asyncio.run(generate())
