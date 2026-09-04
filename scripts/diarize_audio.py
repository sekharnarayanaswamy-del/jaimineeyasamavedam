"""
Speaker Diarization & Audio Separation Script (SpeechBrain & Pyannote)
======================================================================
Splits multi-speaker audio recordings into:
1. diarization_timestamps.csv (Detailed timeline of who spoke when)
2. Individual speaker audio clips in dedicated subfolders
3. Full merged continuous audio track for each speaker

Default Engine: SpeechBrain ECAPA-TDNN (Open, Fast, NO Hugging Face token required)
Optional Engine: Pyannote 3.1 / 4.x (Requires HF token & gated access)

Supports both GPU (CUDA) and CPU automatically.
Uses `soundfile` + `numpy` for fast audio slicing without external ffmpeg.
"""

import os
import sys
import csv
import argparse
import warnings
import numpy as np

# Suppress unnecessary deprecation / future warnings
warnings.filterwarnings("ignore")

def parse_args():
    parser = argparse.ArgumentParser(description="Speaker Diarization and Audio Separation Tool")
    parser.add_argument(
        "-i", "--input",
        type=str,
        default=r"D:\JSV class\JSV class Sep 3.mp3",
        help="Path to the input audio file (.mp3, .wav, .m4a, etc.)"
    )
    parser.add_argument(
        "-o", "--output-dir",
        type=str,
        default=r"D:\JSV class\separated_speakers",
        help="Directory where separated tracks and timestamp CSV will be saved"
    )
    parser.add_argument(
        "--engine",
        type=str,
        choices=["speechbrain", "pyannote"],
        default="speechbrain",
        help="Diarization engine to use (default: 'speechbrain' which requires NO token)"
    )
    parser.add_argument(
        "--num-speakers",
        type=int,
        default=None,
        help="Known number of speakers (optional, e.g. 2 or 3)"
    )
    parser.add_argument(
        "--hf-token",
        type=str,
        default=None,
        help="Hugging Face User Access Token (only needed if using --engine pyannote)"
    )
    parser.add_argument(
        "--device",
        type=str,
        choices=["cuda", "cpu", "auto"],
        default="auto",
        help="Device to run inference on ('cuda', 'cpu', or 'auto')"
    )
    parser.add_argument(
        "--no-clips",
        action="store_true",
        help="Disable exporting individual snippet clips (only export merged tracks & CSV)"
    )
    return parser.parse_args()


def check_dependencies(engine):
    missing = []
    try:
        import torch
    except ImportError:
        missing.append("torch")
    try:
        import soundfile
    except ImportError:
        missing.append("soundfile")

    if engine == "speechbrain":
        try:
            import speechbrain
        except ImportError:
            missing.append("speechbrain")
        try:
            import sklearn
        except ImportError:
            missing.append("scikit-learn")
    elif engine == "pyannote":
        try:
            import pyannote.audio
        except ImportError:
            missing.append("pyannote.audio")

    if missing:
        print("\n[ERROR] Missing required packages:")
        print(f"  Run: pip install {' '.join(missing)}")
        sys.exit(1)


def diarize_with_speechbrain(audio_data, sample_rate, num_speakers, device_name):
    """
    Robust VAD + SpeechBrain ECAPA-TDNN Speaker Embeddings + Agglomerative Clustering.
    Requires ZERO Hugging Face tokens or gated repo approvals.
    """
    import torch
    import torchaudio.transforms as T
    from speechbrain.inference.speaker import EncoderClassifier
    from sklearn.cluster import AgglomerativeClustering
    from sklearn.metrics import silhouette_score

    print("    Loading SpeechBrain ECAPA-TDNN embedding model...")
    classifier = EncoderClassifier.from_hparams(
        source="speechbrain/spkrec-ecapa-voxceleb",
        run_opts={"device": device_name}
    )

    # Convert to mono float32 tensor
    if audio_data.ndim > 1:
        audio_mono = audio_data.mean(axis=1)
    else:
        audio_mono = audio_data

    waveform = torch.tensor(audio_mono, dtype=torch.float32).unsqueeze(0)

    # Resample to 16000 Hz if needed (ECAPA-TDNN operates at 16kHz)
    if sample_rate != 16000:
        resampler = T.Resample(orig_freq=sample_rate, new_freq=16000)
        waveform_16k = resampler(waveform).squeeze(0)
    else:
        waveform_16k = waveform.squeeze(0)

    target_sr = 16000
    total_len_s = len(waveform_16k) / target_sr

    # Step 1: Energy & Dynamic Threshold Voice Activity Detection (VAD)
    print("    Detecting active speech segments...")
    frame_dur = 0.03  # 30ms frames
    frame_len = int(frame_dur * target_sr)
    hop_len = int(frame_len // 2)

    # Compute short-term energy
    num_frames = (len(waveform_16k) - frame_len) // hop_len + 1
    if num_frames <= 0:
        return []

    unfolded = waveform_16k.unfold(0, frame_len, hop_len)
    frame_energy = torch.sqrt(torch.mean(unfolded ** 2, dim=1)).numpy()

    # Adaptive threshold for speech vs silence
    q25 = np.percentile(frame_energy, 25)
    q75 = np.percentile(frame_energy, 75)
    vad_threshold = max(q25 + 0.15 * (q75 - q25), 0.005)
    speech_mask = frame_energy > vad_threshold

    # Smooth speech mask (close gaps < 300ms, remove bursts < 200ms)
    min_speech_frames = int(0.20 / (hop_len / target_sr))
    min_silence_frames = int(0.35 / (hop_len / target_sr))

    # Fill short silence gaps
    in_speech = False
    gap_start = 0
    smoothed = speech_mask.copy()
    for i, active in enumerate(speech_mask):
        if active:
            if not in_speech and i - gap_start < min_silence_frames and gap_start > 0:
                smoothed[gap_start:i] = True
            in_speech = True
        else:
            if in_speech:
                gap_start = i
                in_speech = False

    # Extract continuous speech chunks (chunked into max 3.0s subsegments for fine speaker analysis)
    segments = []
    chunk_start = None
    max_chunk_frames = int(2.5 / (hop_len / target_sr))
    min_chunk_frames = int(0.4 / (hop_len / target_sr))

    for i, active in enumerate(smoothed):
        if active and chunk_start is None:
            chunk_start = i
        elif chunk_start is not None:
            chunk_len = i - chunk_start
            if not active or chunk_len >= max_chunk_frames:
                if chunk_len >= min_chunk_frames:
                    s_sec = chunk_start * hop_len / target_sr
                    e_sec = i * hop_len / target_sr
                    segments.append((s_sec, min(e_sec, total_len_s)))
                chunk_start = i if active else None

    if chunk_start is not None and (len(smoothed) - chunk_start) >= min_chunk_frames:
        segments.append((chunk_start * hop_len / target_sr, total_len_s))

    if not segments:
        print("    [WARNING] No speech segments found.")
        return []

    print(f"    Found {len(segments)} speech segments. Extracting speaker embeddings...")

    # Step 2: Extract ECAPA-TDNN embeddings per segment
    embeddings = []
    valid_segments = []

    for s_sec, e_sec in segments:
        s_idx = int(s_sec * target_sr)
        e_idx = int(e_sec * target_sr)
        sub_wave = waveform_16k[s_idx:e_idx].unsqueeze(0).to(device_name)

        if sub_wave.shape[1] < int(0.3 * target_sr):
            continue

        with torch.no_grad():
            emb = classifier.encode_batch(sub_wave)
            emb = emb.squeeze().cpu().numpy()
            # Normalize embedding vector
            norm = np.linalg.norm(emb)
            if norm > 0:
                emb = emb / norm
            embeddings.append(emb)
            valid_segments.append((s_sec, e_sec))

    embeddings = np.array(embeddings)
    if len(embeddings) < 2:
        return [(valid_segments[0][0], valid_segments[0][1], "SPEAKER_00")]

    # Step 3: Clustering to separate speakers
    print("    Clustering speaker vectors...")
    if num_speakers is None:
        best_k = 2
        best_score = -1
        max_k = min(5, len(embeddings) - 1)
        for k in range(2, max_k + 1):
            try:
                clusterer = AgglomerativeClustering(n_clusters=k, metric="cosine", linkage="average")
                labels_test = clusterer.fit_predict(embeddings)
                if len(set(labels_test)) > 1:
                    score = silhouette_score(embeddings, labels_test, metric="cosine")
                    if score > best_score:
                        best_score = score
                        best_k = k
            except Exception:
                pass
        num_speakers = best_k

    clusterer = AgglomerativeClustering(n_clusters=num_speakers, metric="cosine", linkage="average")
    labels = clusterer.fit_predict(embeddings)

    # Step 4: Merge adjacent segments of the same speaker if within 0.5s
    labeled_segments = []
    for (s_sec, e_sec), label in zip(valid_segments, labels):
        spk_name = f"SPEAKER_{label:02d}"
        if labeled_segments and labeled_segments[-1]["speaker"] == spk_name and (s_sec - labeled_segments[-1]["end_s"]) < 0.5:
            labeled_segments[-1]["end_s"] = e_sec
        else:
            labeled_segments.append({
                "start_s": s_sec,
                "end_s": e_sec,
                "speaker": spk_name
            })

    return labeled_segments


def diarize_with_pyannote(audio_path, hf_token, num_speakers, device_name):
    """
    Pyannote pipeline (Requires HF token & gated access).
    """
    import torch
    from pyannote.audio import Pipeline

    try:
        try:
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                token=hf_token
            )
        except TypeError:
            pipeline = Pipeline.from_pretrained(
                "pyannote/speaker-diarization-3.1",
                use_auth_token=hf_token
            )
    except Exception as e:
        print(f"\n[ERROR] Failed to load Pyannote pipeline: {e}")
        sys.exit(1)

    pipeline.to(torch.device(device_name))

    if num_speakers:
        diarization = pipeline(audio_path, num_speakers=num_speakers)
    else:
        diarization = pipeline(audio_path)

    labeled_segments = []
    for turn, _, speaker in diarization.itertracks(yield_label=True):
        labeled_segments.append({
            "start_s": turn.start,
            "end_s": turn.end,
            "speaker": speaker
        })
    return labeled_segments


def main():
    args = parse_args()
    check_dependencies(args.engine)

    import torch
    import soundfile as sf

    audio_path = os.path.abspath(args.input)
    output_dir = os.path.abspath(args.output_dir)

    if not os.path.exists(audio_path):
        print(f"[ERROR] Audio file not found: {audio_path}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    # Determine device
    if args.device == "auto":
        device_name = "cuda" if torch.cuda.is_available() else "cpu"
    else:
        device_name = args.device

    print(f"\n==========================================")
    print(f" Speaker Diarization & Voice Separation")
    print(f"==========================================")
    print(f" Input File   : {audio_path}")
    print(f" Output Dir   : {output_dir}")
    print(f" Engine       : {args.engine.upper()}")
    print(f" Device       : {device_name} ({torch.cuda.get_device_name(0) if device_name == 'cuda' else 'CPU'})")
    if args.num_speakers:
        print(f" Speakers     : {args.num_speakers} (specified)")
    else:
        print(f" Speakers     : Auto-detect")
    print(f"==========================================\n")

    # 1. Load Audio
    print(f"--> [1/4] Loading audio file...")
    audio_data, sample_rate = sf.read(audio_path)
    total_samples = len(audio_data)
    total_duration_s = total_samples / sample_rate
    print(f"    Loaded successfully ({total_duration_s:.1f}s / {int(total_duration_s//60)}m {int(total_duration_s%60)}s, {sample_rate}Hz)")

    # 2. Run Diarization
    print(f"--> [2/4] Running {args.engine} speaker analysis...")
    if args.engine == "speechbrain":
        raw_segments = diarize_with_speechbrain(audio_data, sample_rate, args.num_speakers, device_name)
    else:
        hf_token = args.hf_token or os.environ.get("HF_TOKEN")
        raw_segments = diarize_with_pyannote(audio_path, hf_token, args.num_speakers, device_name)

    if not raw_segments:
        print("[ERROR] No speaker segments were detected.")
        sys.exit(1)

    # 3. Build Detailed Report & Timeline CSV
    print(f"--> [3/4] Generating timestamp CSV report...")
    csv_path = os.path.join(output_dir, "diarization_timestamps.csv")
    segments = []

    with open(csv_path, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(["Index", "Speaker", "Start_sec", "End_sec", "Duration_sec", "Start_MMSS", "End_MMSS"])

        for i, item in enumerate(raw_segments, start=1):
            s_sec = round(item["start_s"], 2)
            e_sec = round(item["end_s"], 2)
            dur_s = round(e_sec - s_sec, 2)
            if dur_s <= 0.05:
                continue

            start_sample = int(s_sec * sample_rate)
            end_sample = min(int(e_sec * sample_rate), total_samples)

            start_fmt = f"{int(s_sec // 60):02d}:{int(s_sec % 60):02d}"
            end_fmt = f"{int(e_sec // 60):02d}:{int(e_sec % 60):02d}"

            writer.writerow([i, item["speaker"], s_sec, e_sec, dur_s, start_fmt, end_fmt])
            segments.append({
                "index": i,
                "speaker": item["speaker"],
                "start_sample": start_sample,
                "end_sample": end_sample,
                "start_s": s_sec,
                "end_s": e_sec,
                "dur_s": dur_s,
                "start_fmt": start_fmt,
                "end_fmt": end_fmt,
            })

    unique_speakers = sorted(list(set(s["speaker"] for s in segments)))
    print(f"    Detected {len(unique_speakers)} speaker(s): {', '.join(unique_speakers)}")
    print(f"    Total speech turns: {len(segments)}")
    print(f"    Timeline saved to: {csv_path}")

    # 4. Slicing and Exporting Audio Files
    print(f"--> [4/4] Exporting isolated tracks and clips...")
    speaker_chunks = {spk: [] for spk in unique_speakers}

    if not args.no_clips:
        for spk in unique_speakers:
            os.makedirs(os.path.join(output_dir, spk), exist_ok=True)

    for seg in segments:
        spk = seg["speaker"]
        idx = seg["index"]
        clip_data = audio_data[seg["start_sample"]:seg["end_sample"]]

        if not args.no_clips:
            clip_file = os.path.join(
                output_dir, spk, f"clip_{idx:04d}_{int(seg['start_s'])}s_to_{int(seg['end_s'])}s.wav"
            )
            sf.write(clip_file, clip_data, sample_rate)

        speaker_chunks[spk].append(clip_data)

    print("\n  Merged Output Tracks:")
    for spk, chunks in speaker_chunks.items():
        if chunks:
            merged_data = np.concatenate(chunks, axis=0)
            dur_mins = len(merged_data) / sample_rate / 60.0
            out_file = os.path.join(output_dir, f"{spk}_all_merged.wav")
            sf.write(out_file, merged_data, sample_rate)
            print(f"    - {spk}: {out_file} ({dur_mins:.2f} mins total speaking)")

    print(f"\n[SUCCESS] Separation complete! All files saved in:\n  {output_dir}\n")


if __name__ == "__main__":
    main()
