---

# MultiAV S3 Scanner

A scalable, multi-engine antivirus scanning system for AWS S3 objects using an SQS-driven workflow.

This service downloads files from S3, scans them with multiple antivirus engines (Sophos, ClamAV, McAfee), and applies results back to the object via tags and routing logic.

---

## 🚀 Features

* Multi-engine AV scanning (Sophos, ClamAV, McAfee)
* SQS-driven, event-based architecture
* Recursive archive extraction (zip, tar, gz, etc.)
* S3 object tagging with scan results
* Infected file quarantine
* Error handling (corrupt, password-protected files)
* Slack notifications for large files
* Datadog metrics support
* Automatic cleanup of temp scan directories

---

## 🏗️ Architecture

S3 Upload → S3 Event → SQS → Scanner → AV Engines → Result Handling

Results:

* CLEAN → sent to output queue
* INFECTED → moved to infected bucket
* ERROR → moved to unscanned bucket

---

## 📂 Project Structure

```
.
├── scan.py
├── core.py
├── common.py
├── multiav_s3_scanner.py
├── scan_bucket.py
├── slack_notify.py
├── metrics.py
├── file_filter.py
├── provider_info.py
├── update.py
├── config.cfg
```

---

## ⚙️ How It Works

1. S3 object upload triggers an event sent to SQS
2. Scanner pulls messages from SQS
3. File is downloaded locally (typically `/tmp/s3_scan`)
4. Archives are extracted recursively
5. Each file is scanned by all configured AV engines
6. Results are aggregated
7. Object is tagged and routed based on result

---

## 🧠 Scan Results

Each engine returns results per file path.

Final result is normalized into:

* CLEAN
* INFECTED
* ERROR

Example:

```
Engines: Sophos:ClamAV:McAfee
Signatures: EICAR-Test:OK:OK
Result: INFECTED
```

---

## 🏷️ S3 Tags

Each scanned object is tagged with:

* `av-status` → CLEAN | INFECTED | ERROR
* `av-signatures` → detected signatures
* `av-engines` → engines used
* `av-versions` → engine versions
* `av-timestamp` → scan time
* `av-mime` → MIME type
* `av-sqs-name` → source queue

---

## 🧪 Supported Archive Types

* zip
* tar
* gz / tgz
* bz2
* xz
* 7z
* rar

Nested archives are supported.

---

## 🛠️ Requirements

* Python 3.8+
* AWS credentials configured
* Access to S3 and SQS
* Installed AV engines:

  * Sophos SPL
  * ClamAV
  * McAfee (uvscan)

---

## 📦 Installation

```
pip install boto3 python-magic pyunpack patool watchdog
```

---

## ▶️ Usage

```
python scan.py \
  --sqs <INPUT_SQS_QUEUE> \
  --output <OUTPUT_SQS_QUEUE> \
  --infected <INFECTED_BUCKET> \
  --prefix /tmp/s3_scan \
  --config config.cfg \
  --batch 10 \
  --engine ALL
```

Optional:

```
--sequential True
```

---

## ⚙️ Configuration

Configured via environment variables and `config.cfg`.

Key settings:

* INPUT_SQS_PATH
* OUTPUT_SQS_PATH
* INFECTED_BUCKET
* S3_PREFIX
* AWS_CERT_VERIFY
* AV_PROCESS_ORIGINAL_VERSION_ONLY

---

## 🧵 Concurrency

* Downloads are threaded
* Scans can run:

  * Parallel (default)
  * Sequential

---

## 🚨 Error Handling

Handles:

* Corrupt archives
* Password-protected files
* Extraction failures
* AV engine errors

Errors are stored as:

```
('ERROR', '<reason>')
```

---

## 📊 Metrics

Emits Datadog metrics:

* s3_antivirus.scanned
* s3_antivirus.clean
* s3_antivirus.infected

---

## 📣 Notifications

Slack alerts triggered for large files (e.g. ≥ 2GB)

Includes:

* bucket
* key
* size
* MIME type

---

## 🧹 Cleanup

* Temporary scan directory is removed after processing
* Empty directories cleaned up automatically

---

## 🧪 Debugging

Check logs:

```
/var/log/sophos/
/var/log/multiav/
```

Check SQS:

```
aws sqs receive-message --queue-url <QUEUE_URL>
```

---

## ⚠️ Known Limitations

* Large archives can be slow
* Deep nesting impacts performance
* Password-protected files cannot be scanned
* AV engines may return inconsistent signatures

---

## 🔮 Future Improvements

* Stream-based scanning (no full extraction)
* Improved archive validation
* Better error classification
* Enhanced per-engine isolation
* Store logs in S3 metadata instead of tags

---

## 📄 License

Apache License 2.0
Sophos subcription
McAfee Subcription

---
