import os
import logging
import whisper
import tempfile
import subprocess
from typing import List
from dotenv import load_dotenv
from unstructured.partition.auto import partition
from langchain.text_splitter import RecursiveCharacterTextSplitter

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv(".env")

def load_files(file_paths: List[str]) -> str:
    """
    Loads and processes data from a list of file paths.

    For each file path, this function checks if the file exists.
    If the file exists, it uses the unstructured.partition.auto module
    to partition the file's content and convert it into a string format.
    The processed data is then appended to a full text string, prefixed
    by the file's basename without its extension.

    Args:
        file_paths (list[str]): A list of file paths to be loaded and processed.

    Returns:
        str: A concatenated string containing the processed content from
        all valid files, separated by double newlines.
    """
    logger.info("🚀 Start Loading Data ...")
    full_text = ""
    for path in file_paths:
        try:
            # Load Data Using Unstructured Library
            result = partition(path)
            data = "\n\n".join([str(el) for el in result])
            
            # Add Data to Full Text
            filename = os.path.basename(path).split(".")[0]
            full_text += f"## {filename}" + "\n\n" + data + "\n---\n"
        
        except Exception as e:
            logger.error(f"Error processing file {path}: {e}")
            continue
        
    logger.info("✅ Finished loading data.")
    return full_text



def extract_transcription(video_path):
    model = whisper.load_model("./models/whisper_models/base.pt")
    
    with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as temp_audio:
        temp_audio_path = temp_audio.name
    
    try:
        # Extract audio from video using ffmpeg
        command = ["ffmpeg", "-i", video_path, "-ac", "1", "-ar", "16000", "-vn", temp_audio_path, "-y" ]
        subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, check=True)
        
        # Transcribe the audio
        result = model.transcribe(temp_audio_path)
        return result["text"]
    
    finally:
        # Cleanup temporary audio file
        if os.path.exists(temp_audio_path):
            os.remove(temp_audio_path)


def load_data(text_data: str) -> List[str]:
    """
    Processes the input text data by splitting it into chunks.

    This function takes a string of text data, splits it into
    smaller chunks using a RecursiveCharacterTextSplitter, and
    returns a list of these chunks. If no text data is provided,
    an error is logged and None is returned.

    Args:
        text_data (str): The input text data to be split.

    Returns:
        list[str]: A list of text chunks obtained by splitting
        the input text data, or None if the input is empty.
    """
    if not text_data:
        logger.error(f"Error Data not Found file.")
        return None

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000,
                                              chunk_overlap=200)
    doc = splitter.split_text(text_data)
    return doc