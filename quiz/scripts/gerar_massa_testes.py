# -*- coding: utf-8 -*-
"""
Gera massa de dados para testes com ~105 contatos em diferentes etapas do funil,
distribuídos ao longo do dia 26/09/2026, com telemetria completa em dados/eventos/2026-09-26.jsonl
e leituras correspondentes em dados/leituras/*.json.
"""
import json
import random
import uuid
from datetime import datetime, date, timedelta, timezone
from pathlib import Path

FUSO_BSB = timezone(timedelta(hours=-3))

NOMES_PRIMEIROS_F = [
    "Juliana", "Camila", "Larissa", "Mariana", "Fernanda", "Bruna", "Amanda", "Letícia",
    "Beatriz", "Gabriela", "Patrícia", "Aline", "Jéssica", "Rafaela", "Bianca", "Vanessa",
    "Carla", "Daniela", "Priscila", "Renata", "Carolina", "Thaís", "Débora", "Luana",
    "Natália", "Sabrina", "Taís", "Clarice", "Viviane", "Helena", "Isabela", "Cláudia"
]

NOMES_PRIMEIROS_M = [
    "Lucas", "Mateus", "Gabriel", "Rodrigo", "Felipe", "Thiago", "Gustavo", "Guilherme",
    "Leonardo", "Bruno", "Eduardo", "Rafael", "Vinícius", "Diego", "Marcelo", "Alexandre",
    "Daniel", "Fernando", "André", "Henrique", "Caio", "Vitor", "Leandro", "Ricardo",
    "Renan", "Murilo", "Igor", "Arthur", "Danilo", "Samuel", "Fábio", "Otávio"
]

SOBRENOMES = [
    "Silva", "Santos", "Oliveira", "Souza", "Rodrigues", "Ferreira", "Alves", "Pereira",
    "Lima", "Gomes", "Costa", "Ribeiro", "Martins", "Carvalho", "Almeida", "Lopes",
    "Soares", "Fernandes", "Vieira", "Barbosa", "Rocha", "Dias", "Nascimento", "Andrade",
    "Moreira", "Nunes", "Marques", "Machado", "Mendes", "Freitas", "Cardoso", "Ramos",
    "Gonçalves", "Santana", "Teixeira", "Araújo", "Castro", "Cavalcanti", "Macedo", "Moraes"
]

CIDADES_UF = [
    ("São Paulo", "SP", "São Paulo", -23.5505, -46.6333, "America/Sao_Paulo", "11"),
    ("Campinas", "SP", "São Paulo", -22.9056, -47.0608, "America/Sao_Paulo", "19"),
    ("Ribeirão Preto", "SP", "São Paulo", -21.1767, -47.8208, "America/Sao_Paulo", "16"),
    ("Rio de Janeiro", "RJ", "Rio de Janeiro", -22.9068, -43.1729, "America/Sao_Paulo", "21"),
    ("Niterói", "RJ", "Rio de Janeiro", -22.8833, -43.1036, "America/Sao_Paulo", "21"),
    ("Belo Horizonte", "MG", "Minas Gerais", -19.9208, -43.9378, "America/Sao_Paulo", "31"),
    ("Uberlândia", "MG", "Minas Gerais", -18.9186, -48.2772, "America/Sao_Paulo", "34"),
    ("Curitiba", "PR", "Paraná", -25.4284, -49.2733, "America/Sao_Paulo", "41"),
    ("Londrina", "PR", "Paraná", -23.3103, -51.1628, "America/Sao_Paulo", "43"),
    ("Porto Alegre", "RS", "Rio Grande do Sul", -30.0346, -51.2177, "America/Sao_Paulo", "51"),
    ("Caxias do Sul", "RS", "Rio Grande do Sul", -29.1678, -51.1794, "America/Sao_Paulo", "54"),
    ("Florianópolis", "SC", "Santa Catarina", -27.5954, -48.5480, "America/Sao_Paulo", "48"),
    ("Salvador", "BA", "Bahia", -12.9714, -38.5014, "America/Bahia", "71"),
    ("Recife", "PE", "Pernambuco", -8.0476, -34.8770, "America/Recife", "81"),
    ("Fortaleza", "CE", "Ceará", -3.7172, -38.5431, "America/Fortaleza", "85"),
    ("Brasília", "DF", "Distrito Federal", -15.7975, -47.8919, "America/Sao_Paulo", "61"),
    ("Goiânia", "GO", "Goiás", -16.6869, -49.2648, "America/Sao_Paulo", "62"),
    ("Belém", "PA", "Pará", -1.4558, -48.4902, "America/Belem", "91"),
    ("Vitória", "ES", "Espírito Santo", -20.3155, -40.3128, "America/Sao_Paulo", "27"),
    ("Campo Grande", "MS", "Mato Grosso do Sul", -20.4697, -54.6201, "America/Campo_Grande", "67")
]

AREAS_QUIZ = [
    ("amor", "Estou só e não sei se por escolha ou por medo"),
    ("amor", "Sinto que estou me anulando na minha relação"),
    ("trabalho", "Sinto que cheguei a um teto e não sei para onde crescer"),
    ("trabalho", "Quero mudar de área mas tenho receio da instabilidade"),
    ("dinheiro", "O dinheiro entra e sai sem que eu consiga reter nada"),
    ("dinheiro", "Preciso destravar meus ganhos e cobrar o valor justo"),
    ("familia", "Carrego responsabilidades familiares que não são minhas"),
    ("espiritualidade", "Sinto um chamado interno mas não sei como praticar"),
]


def gerar_dados(dir_leituras: Path, dir_eventos: Path, total_leituras: int = 105, abandonos_iniciais: int = 35):
    dir_leituras.mkdir(parents=True, exist_ok=True)
    dir_eventos.mkdir(parents=True, exist_ok=True)

    data_hoje = date(2026, 9, 26)
    arq_eventos = dir_eventos / f"{data_hoje:%Y-%m-%d}.jsonl"

    random.seed(42)  # repetível e consistente

    eventos_linhas = []
    
    # Se já existir arquivo de eventos de hoje, mantemos os existentes que não sejam de testes automáticos repetidos
    linhas_existentes = []
    if arq_eventos.exists():
        for l in arq_eventos.read_text(encoding="utf-8").splitlines():
            if l.strip():
                try:
                    ev = json.loads(l)
                    linhas_existentes.append(ev)
                except Exception:
                    pass

    # 1. Gerar visitantes que abandonaram antes da entrega da carta (telas 1 a 6)
    horario_base = datetime(2026, 9, 26, 8, 15, 0, tzinfo=FUSO_BSB)
    
    for i in range(abandonos_iniciais):
        sid = str(uuid.uuid4())
        aid = str(uuid.uuid4())
        delta_min = random.randint(5, 360)
        ts_atual = horario_base + timedelta(minutes=delta_min, seconds=random.randint(0, 59))
        seq = 1
        disp = random.choice(["movel", "movel", "movel", "desktop"])

        eventos_linhas.append({
            "v": 1, "ts": ts_atual.isoformat(timespec="seconds"), "ts_cli": int(ts_atual.timestamp() * 1000),
            "seq": seq, "sid": sid, "aid": aid, "evt": "sessao_inicio", "props": {},
            "disp": disp, "bot": False, "teste": False
        })

        parou_na_tela = random.choices([1, 2, 3, 4, 5, 6], weights=[15, 20, 25, 15, 20, 5])[0]
        ms_acumulado = 0

        for t in range(1, parou_na_tela + 1):
            seq += 1
            dur_tela = random.randint(4000, 18000)
            ms_acumulado += dur_tela
            ts_atual += timedelta(milliseconds=dur_tela)
            props_tela = {"de": t - 1, "para": t, "ms_na_anterior": dur_tela, "ms_acumulado": ms_acumulado}
            eventos_linhas.append({
                "v": 1, "ts": ts_atual.isoformat(timespec="seconds"), "ts_cli": int(ts_atual.timestamp() * 1000),
                "seq": seq, "sid": sid, "aid": aid, "evt": "tela", "props": props_tela,
                "disp": disp, "bot": False, "teste": False
            })

            if t == 1:
                seq += 1
                area, espelho = random.choice(AREAS_QUIZ)
                eventos_linhas.append({
                    "v": 1, "ts": ts_atual.isoformat(timespec="seconds"), "ts_cli": int(ts_atual.timestamp() * 1000),
                    "seq": seq, "sid": sid, "aid": aid, "evt": "escolha", "props": {"campo": "area", "valor": area},
                    "disp": disp, "bot": False, "teste": False
                })

    # 2. Gerar as 105 leituras com pessoas reais em diferentes fases do funil
    leituras_geradas = 0

    for i in range(total_leituras):
        sid = str(uuid.uuid4())
        aid = str(uuid.uuid4())
        
        # Horário entre 08:30 e 14:40
        minutos_dia = int((i / total_leituras) * 360) + random.randint(0, 5)
        dt_chegada_bsb = horario_base + timedelta(minutes=minutos_dia, seconds=random.randint(0, 50))
        
        # Gênero e nome
        eh_mulher = random.random() < 0.65
        p_nome = random.choice(NOMES_PRIMEIROS_F if eh_mulher else NOMES_PRIMEIROS_M)
        s_nomes = " ".join(random.sample(SOBRENOMES, 2))
        nome_completo = f"{p_nome} {s_nomes}".upper()

        # Cidade e DDD
        cid_nome, uf_sigla, uf_extenso, lat, lng, tz, ddd = random.choice(CIDADES_UF)

        # WhatsApp (82% preenchem whatsapp)
        tem_wa = random.random() < 0.82
        if tem_wa:
            n9 = random.randint(91000000, 99999999)
            whatsapp = f"+55 ({ddd}) 9{n9 // 10000}-{n9 % 10000:04d}"
        else:
            whatsapp = None

        # Data de nascimento (idades entre 19 e 68 anos)
        ano_nasc = random.randint(1958, 2007)
        mes_nasc = random.randint(1, 12)
        dia_nasc = random.randint(1, 28)
        hora_nasc = random.randint(0, 23)
        min_nasc = random.randint(0, 59)
        precisao_hora = random.choices(["exata", "aproximada", "nao_sei"], weights=[65, 25, 10])[0]

        # Tempos de quiz realistas
        duracao_total_ms = random.randint(38000, 210000)  # 38s a 3m30s
        tempo_ativo_ms = int(duracao_total_ms * random.uniform(0.85, 0.98))

        dt_gerada_bsb = dt_chegada_bsb + timedelta(milliseconds=duracao_total_ms)

        # ID da leitura com padrão oficial YYYYMMDD-HHMMSS-xxxxxxxx
        lid_data_str = dt_gerada_bsb.strftime("%Y%m%d-%H%M%S")
        lid_hex = uuid.uuid4().hex[:8]
        leitura_id = f"{lid_data_str}-{lid_hex}"

        # Etapa máxima alcançada no funil
        # 105 pessoas:
        # ~20 param na Tela 7 (Leitura)
        # ~18 param na Tela 8
        # ~15 param na Tela 9
        # ~22 param na Tela 10 (Oferta sem checkout)
        # ~30 clicam em Checkout (Tela 10 com checkout)
        sorteio_funil = random.random()
        if sorteio_funil < 0.18:
            etapa_max = 7
            etapa_nome = "Tela 7 (Leitura)"
            teve_checkout = False
            comprou = False
        elif sorteio_funil < 0.34:
            etapa_max = 8
            etapa_nome = "Tela 8 (Desdobramento)"
            teve_checkout = False
            comprou = False
        elif sorteio_funil < 0.48:
            etapa_max = 9
            etapa_nome = "Tela 9 (Aprofundamento)"
            teve_checkout = False
            comprou = False
        elif sorteio_funil < 0.70:
            etapa_max = 10
            etapa_nome = "Tela 10 (Oferta)"
            teve_checkout = False
            comprou = False
        else:
            # Foram ao checkout! (~30% dos leads)
            etapa_max = 10
            etapa_nome = "✦ Clique no Checkout"
            teve_checkout = True
            # Dentre os que foram ao checkout, alguns compraram (~25% dos que foram ao checkout)
            comprou = random.random() < 0.28

        # Avaliação com estrelas (65% avaliam)
        if random.random() < 0.65:
            feedback_estrelas = random.choices([5, 4, 3, 2, 1], weights=[55, 30, 10, 3, 2])[0]
            feedback_pulou = False
        elif random.random() < 0.15:
            feedback_estrelas = None
            feedback_pulou = True
        else:
            feedback_estrelas = None
            feedback_pulou = False

        area, espelho = random.choice(AREAS_QUIZ)

        # Meta de custos de IA
        tokens_in = random.randint(24000, 34000)
        tokens_out = random.randint(1200, 2200)
        custo_usd = round((tokens_in * 0.0025 + tokens_out * 0.010) / 1000, 6)
        ms_llm = random.randint(14000, 28000)

        # Monta objeto da leitura JSON
        leitura_doc = {
            "cliente_id": sid,
            "nome_completo": nome_completo,
            "whatsapp": whatsapp,
            "nascimento": {
                "ano": ano_nasc,
                "mes": mes_nasc,
                "dia": dia_nasc,
                "hora": hora_nasc,
                "minuto": min_nasc,
                "precisao": precisao_hora,
                "periodo": None,
                "is_dst": None
            },
            "cidade": {
                "nome": cid_nome,
                "uf": uf_extenso,
                "pais": "Brasil",
                "cc": "BR",
                "lat": lat,
                "lng": lng,
                "tz": tz
            },
            "quiz": {
                "area": area,
                "espelho": espelho,
                "espelho_idx": random.randint(0, 3),
                "quebra": "nao"
            },
            "tempo_quiz_ms": duracao_total_ms,
            "tempo_ativo_ms": tempo_ativo_ms,
            "etapa_max": etapa_max,
            "etapa_nome": etapa_nome,
            "checkout": teve_checkout,
            "comprou": comprou,
            "feedback_estrelas": feedback_estrelas,
            "feedback_pulou": feedback_pulou,
            "meta": {
                "modelo": "gpt-5.6-luna",
                "tentativas": random.choice([1, 1, 1, 2]),
                "validacao": "sucesso",
                "ms_llm": ms_llm,
                "prompt_tokens": tokens_in,
                "completion_tokens": tokens_out,
                "total_tokens": tokens_in + tokens_out,
                "custo_usd": custo_usd,
                "ms": {
                    "astro": random.randint(10, 25),
                    "total": ms_llm + 20
                }
            },
            "carta": {
                "titulo": f"Direção para {area}",
                "destaque": "Uma decisão firme vale mais do que semanas tentando agradar a todos ao redor.",
                "selo": f"Trânsito astrológico na Casa {random.randint(1, 12)}",
                "saudacao": f"{p_nome.upper()},",
                "paragrafos": [
                    f"Você trouxe uma questão importante sobre {area}. Este é um momento onde o céu aponta para escolhas autênticas.",
                    "Não adie o que pede posicionamento claro. Ao assumir o que sente, o caminho se organiza com menor desgaste."
                ],
                "janela": "nas próximas semanas",
                "assinatura": f"Escrita para {cid_nome}, {dia_nasc}/{mes_nasc}/{ano_nasc}."
            },
            "gravado_em": dt_gerada_bsb.astimezone(timezone.utc).isoformat(),
            "gravado_em_bsb": dt_gerada_bsb.strftime("%d/%m/%y %H:%M"),
            "chegou_em_bsb": dt_chegada_bsb.strftime("%d/%m/%y %H:%M")
        }

        # Salva o arquivo de leitura
        caminho_leitura = dir_leituras / f"{leitura_id}.json"
        caminho_leitura.write_text(json.dumps(leitura_doc, ensure_ascii=False, indent=2), encoding="utf-8")
        leituras_geradas += 1

        # Gera os eventos de telemetria correspondentes
        seq = 1
        disp = random.choice(["movel", "movel", "movel", "desktop"])
        ts_corr = dt_chegada_bsb

        # 1. sessao_inicio
        eventos_linhas.append({
            "v": 1, "ts": ts_corr.isoformat(timespec="seconds"), "ts_cli": int(ts_corr.timestamp() * 1000),
            "seq": seq, "sid": sid, "aid": aid, "evt": "sessao_inicio", "props": {},
            "disp": disp, "bot": False, "teste": False
        })

        ms_acum = 0
        passos_telas = min(etapa_max, 10)
        
        for t in range(1, passos_telas + 1):
            seq += 1
            ms_t = int(duracao_total_ms / (passos_telas + 2))
            ms_acum += ms_t
            ts_corr += timedelta(milliseconds=ms_t)
            eventos_linhas.append({
                "v": 1, "ts": ts_corr.isoformat(timespec="seconds"), "ts_cli": int(ts_corr.timestamp() * 1000),
                "seq": seq, "sid": sid, "aid": aid, "evt": "tela",
                "props": {"de": t - 1, "para": t, "ms_na_anterior": ms_t, "ms_acumulado": ms_acum},
                "disp": disp, "bot": False, "teste": False
            })

            if t == 1:
                seq += 1
                eventos_linhas.append({
                    "v": 1, "ts": ts_corr.isoformat(timespec="seconds"), "ts_cli": int(ts_corr.timestamp() * 1000),
                    "seq": seq, "sid": sid, "aid": aid, "evt": "escolha", "props": {"campo": "area", "valor": area},
                    "disp": disp, "bot": False, "teste": False
                })
            elif t == 5:
                seq += 1
                eventos_linhas.append({
                    "v": 1, "ts": ts_corr.isoformat(timespec="seconds"), "ts_cli": int(ts_corr.timestamp() * 1000),
                    "seq": seq, "sid": sid, "aid": aid, "evt": "form_envio", "props": {"area": area, "modo_hora": precisao_hora},
                    "disp": disp, "bot": False, "teste": False
                })

        # Evento leitura_entregue
        seq += 1
        ts_corr += timedelta(seconds=2)
        eventos_linhas.append({
            "v": 1, "ts": ts_corr.isoformat(timespec="seconds"), "ts_cli": int(ts_corr.timestamp() * 1000),
            "seq": seq, "sid": sid, "aid": aid, "evt": "leitura_entregue",
            "props": {"leitura_id": leitura_id, "area": area, "modo_hora": precisao_hora},
            "disp": disp, "bot": False, "teste": False
        })

        # Evento feedback se houver
        if feedback_estrelas:
            seq += 1
            ts_corr += timedelta(seconds=5)
            eventos_linhas.append({
                "v": 1, "ts": ts_corr.isoformat(timespec="seconds"), "ts_cli": int(ts_corr.timestamp() * 1000),
                "seq": seq, "sid": sid, "aid": aid, "evt": "feedback",
                "props": {"nota": feedback_estrelas, "leitura_id": leitura_id},
                "disp": disp, "bot": False, "teste": False
            })

        # Evento oferta_clique se foi ao checkout
        if teve_checkout:
            seq += 1
            ts_corr += timedelta(seconds=12)
            eventos_linhas.append({
                "v": 1, "ts": ts_corr.isoformat(timespec="seconds"), "ts_cli": int(ts_corr.timestamp() * 1000),
                "seq": seq, "sid": sid, "aid": aid, "evt": "oferta_clique",
                "props": {"botao": "principal", "ms_na_tela": 14000, "ms_acumulado": ms_acum + 14000, "leitura_id": leitura_id},
                "disp": disp, "bot": False, "teste": False
            })

    # Grava todos os eventos no arquivo de hoje
    todas_linhas_saida = linhas_existentes + eventos_linhas
    # Ordena por timestamp
    todas_linhas_saida.sort(key=lambda ev: ev.get("ts", ""))

    with open(arq_eventos, "w", encoding="utf-8", newline="\n") as f:
        for ev in todas_linhas_saida:
            f.write(json.dumps(ev, ensure_ascii=False) + "\n")

    print(f"Sucesso! Gerados {leituras_geradas} arquivos de leitura em {dir_leituras}")
    print(f"Telemetria atualizada com {len(todas_linhas_saida)} eventos em {arq_eventos}")


if __name__ == "__main__":
    p_leituras = Path("quiz/dados/leituras")
    p_eventos = Path("quiz/dados/eventos")
    gerar_dados(p_leituras, p_eventos, total_leituras=105, abandonos_iniciais=35)
