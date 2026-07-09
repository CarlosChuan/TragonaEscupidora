#!/usr/bin/env python3
"""
Transcriu els àudios de docs/audio/sessio_*/audio.mp3 amb AssemblyAI
i guarda el resultat a docs/transcripts/sessio_N.txt.

Ús:
  export ASSEMBLYAI_API_KEY="..."
  python transcribe_assemblyai.py                # totes les sessions pendents
  python transcribe_assemblyai.py sessio_5       # només una
  python transcribe_assemblyai.py --force        # re-transcriu encara que existeixi
  python transcribe_assemblyai.py --lang es      # canvia l'idioma (default: ca)
"""

import argparse
import os
import sys
from pathlib import Path

import assemblyai as aai

ROOT = Path(__file__).resolve().parent.parent
AUDIO_DIR = ROOT / "docs" / "audio"
TRANSCRIPTS_DIR = ROOT / "docs" / "transcripts"


def sessions(names: list[str]) -> list[Path]:
    if names:
        dirs = [AUDIO_DIR / n for n in names]
    else:
        dirs = sorted(p for p in AUDIO_DIR.iterdir() if p.is_dir())
    return [d for d in dirs if (d / "audio.mp3").exists()]


def format_transcript(transcript: aai.Transcript) -> str:
    return transcript.text or ""


def transcribe_all(jobs: list[tuple[Path, Path]], language: str) -> None:
    config = aai.TranscriptionConfig(
        language_code=language,
        punctuate=True,
        format_text=True,
    )
    transcriber = aai.Transcriber(config=config)

    futures = []
    for session_dir, out_path in jobs:
        audio = session_dir / "audio.mp3"
        size_mb = audio.stat().st_size / 1024 / 1024
        print(f"▶  {session_dir.name}: enviant {audio.name} ({size_mb:.1f} MB)…", flush=True)
        future = transcriber.transcribe_async(str(audio))
        futures.append((session_dir, out_path, future))

    print(f"\n⏳  {len(futures)} treballs enviats. Esperant resultats en paral·lel…\n", flush=True)

    for session_dir, out_path, future in futures:
        try:
            transcript = future.result()
            if transcript.status == aai.TranscriptStatus.error:
                print(f"❌  {session_dir.name}: {transcript.error}", flush=True)
                continue
            text = format_transcript(transcript)
            out_path.parent.mkdir(parents=True, exist_ok=True)
            out_path.write_text(text, encoding="utf-8")
            words = len(text.split())
            print(f"✓  {session_dir.name}: {words:,} paraules → {out_path.relative_to(ROOT)}", flush=True)
        except Exception as exc:
            print(f"❌  {session_dir.name}: {exc}", flush=True)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("sessions", nargs="*", help="Noms de carpetes de sessió (p.ex. sessio_5). Sense arguments = totes.")
    parser.add_argument("--lang", default="ca", help="Codi ISO d'idioma (default: ca)")
    parser.add_argument("--force", action="store_true", help="Re-transcriu encara que el .txt ja existeixi")
    args = parser.parse_args()

    api_key = os.environ.get("ASSEMBLYAI_API_KEY")
    if not api_key:
        print("❌  Falta ASSEMBLYAI_API_KEY. Exporta la variable d'entorn i torna a executar.", file=sys.stderr)
        sys.exit(1)
    aai.settings.api_key = api_key

    targets = sessions(args.sessions)
    if not targets:
        print("⚠  No hi ha àudios a transcriure a docs/audio/", file=sys.stderr)
        sys.exit(1)

    jobs: list[tuple[Path, Path]] = []
    for session_dir in targets:
        out_path = TRANSCRIPTS_DIR / f"{session_dir.name}.txt"
        if out_path.exists() and not args.force:
            print(f"✓  {session_dir.name}: ja existeix {out_path.name} — saltant (usa --force per re-transcriure)")
            continue
        jobs.append((session_dir, out_path))

    if not jobs:
        print("✓  Res per fer.")
        return

    transcribe_all(jobs, args.lang)


if __name__ == "__main__":
    main()
