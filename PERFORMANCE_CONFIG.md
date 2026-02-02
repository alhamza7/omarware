# Odoo Performance Configuration

## System Specifications

```
CPU Cores: 28
RAM: 62GB
```

## Configuration Applied

### File: `odoo_local.conf`

```ini
# ========================================
# Performance Configuration - Optimized
# ========================================

# Workers: 16 (multiprocessing for CPU utilization)
workers = 16

# Memory Limits: UNLIMITED
limit_memory_soft = 0
limit_memory_hard = 0

# CPU Time Limits: UNLIMITED
limit_time_cpu = 0
limit_time_real = 0
limit_time_real_cron = 0

# Request Limits: UNLIMITED
limit_request = 0

# Database Connections: 128 per worker
db_maxconn = 128

# File Upload: UNLIMITED
limit_upload = 0

# Long Polling: Enabled on port 8072
longpolling_port = 8072
```

---

## Performance Settings Explained

### **1. Workers (Multiprocessing)**

```
workers = 16

Why: Utilize multiple CPU cores
- System has 28 cores
- Using 16 workers for development
- Each worker handles requests independently
- Better concurrency and throughput
```

**Formula for Production:**
```
workers = (CPU cores * 2) + 1
For 28 cores: (28 * 2) + 1 = 57 workers (max recommended)
For development: 16 workers (balanced)
```

---

### **2. Memory Limits: UNLIMITED**

```
limit_memory_soft = 0  # No soft limit
limit_memory_hard = 0  # No hard limit
```

**What this means:**
- Workers can use as much RAM as needed
- No memory restrictions
- Good for:
  - Large reports
  - Big data imports
  - Complex calculations
  - SAP synchronization with many records

**With 62GB RAM:**
- Each worker can use several GB if needed
- No OOM (Out of Memory) kills

---

### **3. CPU Time Limits: UNLIMITED**

```
limit_time_cpu = 0       # No CPU time limit
limit_time_real = 0      # No real-time limit
limit_time_real_cron = 0 # No cron time limit
```

**What this means:**
- Requests can run as long as needed
- No timeout errors for:
  - Long-running reports
  - Large imports/exports
  - Complex SAP synchronization
  - Database operations
  - Batch processing

**Default limits (when not 0):**
- CPU time: 60 seconds
- Real time: 120 seconds
- Cron time: 300 seconds

**Now: No limits!**

---

### **4. Request Limits: UNLIMITED**

```
limit_request = 0
```

**What this means:**
- Workers never restart based on request count
- More stable for long-running processes
- No interruptions during heavy usage

**Default:** 8192 requests before worker restart

---

### **5. Database Connections: 128 per worker**

```
db_maxconn = 128
```

**What this means:**
- Each worker can have up to 128 database connections
- Total potential: 16 workers × 128 = 2048 connections
- No "too many connections" errors
- Better for concurrent operations

---

### **6. File Upload: UNLIMITED**

```
limit_upload = 0
```

**What this means:**
- Can upload files of any size
- No restrictions on:
  - Document attachments
  - Image uploads
  - Import files (CSV, Excel)
  - Backup files

**Default:** 100 MB limit

---

### **7. Long Polling: Enabled**

```
longpolling_port = 8072
```

**What this means:**
- Real-time updates in UI
- Live notifications
- Better user experience
- Separate port for long-polling connections

---

## Performance Impact

### **Before (Default Config):**
```
workers = 0              # Single-threaded
limit_memory_soft = 2048MB
limit_memory_hard = 2560MB
limit_time_cpu = 60s
limit_time_real = 120s
limit_request = 8192
db_maxconn = 64
limit_upload = 100MB
```

**Issues:**
- Single CPU core usage
- Memory limits caused crashes
- Timeout errors on long operations
- Upload size restrictions

---

### **After (Optimized Config):**
```
workers = 16             # Multi-threaded
limit_memory_soft = 0    # UNLIMITED
limit_memory_hard = 0    # UNLIMITED
limit_time_cpu = 0       # UNLIMITED
limit_time_real = 0      # UNLIMITED
limit_request = 0        # UNLIMITED
db_maxconn = 128         # High
limit_upload = 0         # UNLIMITED
```

**Benefits:**
- ✅ Use all 28 CPU cores
- ✅ Use all 62GB RAM as needed
- ✅ No timeout errors
- ✅ No memory limits
- ✅ No upload size limits
- ✅ Better concurrency
- ✅ Faster response times
- ✅ Handle large datasets
- ✅ Long-running operations work

---

## Monitoring Performance

### **Check Worker Processes:**
```bash
ps aux | grep odoo-bin
# Should see 16+ processes (1 master + 16 workers)
```

### **Check Memory Usage:**
```bash
free -h
htop
```

### **Check CPU Usage:**
```bash
top
htop
```

### **Check Database Connections:**
```bash
psql -U capo7amzah -d lugal_local -c "SELECT count(*) FROM pg_stat_activity;"
```

### **Check Logs:**
```bash
tail -f odoo_local.log
```

---

## Ports Used

```
Main HTTP: 8070
Long Polling: 8072
```

---

## When to Use Different Configs

### **Development (Current):**
```
workers = 16
All limits = 0 (unlimited)
```
**Good for:**
- Testing
- Large imports
- Complex operations
- No restrictions

---

### **Production (Recommended):**
```
workers = 40-50 (for 28 cores)
limit_memory_soft = 8192000000  # 8GB
limit_memory_hard = 10240000000 # 10GB
limit_time_cpu = 600            # 10 minutes
limit_time_real = 1200          # 20 minutes
limit_request = 65536           # High but not unlimited
```
**Good for:**
- Controlled resource usage
- Prevent runaway processes
- Better stability
- Multi-tenant environments

---

### **Single User Development:**
```
workers = 0
dev_mode = reload
```
**Good for:**
- Debugging
- Code changes auto-reload
- Simpler process management

---

## Configuration Files

```
Local Development: odoo_local.conf
Remote Server: odoo.conf
```

---

## Testing the Configuration

### **1. Test High CPU Usage:**
```python
# In Odoo, run a complex report
# Or import large dataset
# CPU should distribute across cores
```

### **2. Test Memory Usage:**
```python
# Import 10,000+ products
# Generate large reports
# No memory errors should occur
```

### **3. Test Long Operations:**
```python
# Run SAP synchronization
# Should complete without timeout
# No "Request timeout" errors
```

### **4. Test File Uploads:**
```python
# Upload large files (>100MB)
# Should work without errors
```

---

## Reverting to Safe Defaults

If you need to revert to safe defaults:

```ini
[options]
workers = 4
limit_memory_soft = 2684354560  # 2.5GB
limit_memory_hard = 3221225472  # 3GB
limit_time_cpu = 600            # 10 min
limit_time_real = 1200          # 20 min
limit_request = 8192
db_maxconn = 64
limit_upload = 104857600        # 100MB
```

---

## Summary

```
✅ Workers: 16 (multi-core usage)
✅ Memory: Unlimited
✅ CPU Time: Unlimited
✅ Requests: Unlimited
✅ DB Connections: 128
✅ Upload Size: Unlimited
✅ Long Polling: Enabled

System: 28 cores, 62GB RAM
Config: Optimized for maximum performance
Status: Running on port 8070
```

---

**Performance Mode: MAXIMUM** 🚀

**No limits, full power!** 💪

---

**Created:** 2026-02-01  
**Status:** ✅ Active
