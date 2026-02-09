# RECOVERY CHECKLIST
## Project: Siya
## Version: 1.0.0 (Baseline)

---

## OVERVIEW

This checklist provides step-by-step recovery procedures for Siya system failures.

**Per DIP Phase 9: Production Lock & Baseline**

OpenClaw-inspired capabilities are adopted/adapted in Siya where law-aligned; see `docs/EVOLUTION_ROADMAP.md`.

---

## RECOVERY SCENARIOS

### 1. Power Loss Recovery

**Symptoms:**
- System rebooted unexpectedly
- Incomplete tasks detected
- State files present in automation_state/

**Recovery Steps:**

1. **Check System State**
   ```bash
   python -c "
   from memory import Database
   from system import StateChecker
   db = Database('siya.db')
   db.connect()
   checker = StateChecker(db)
   result = checker.check_state_consistency()
   print(f'Issues: {result[\"issues\"]}')
   "
   ```

2. **Recover State**
   ```bash
   python -c "
   from memory import Database
   from system import StateChecker
   db = Database('siya.db')
   db.connect()
   checker = StateChecker(db)
   result = checker.check_state_consistency()
   if result['issues']:
       checker.recover_state(result['issues'])
   "
   ```

3. **Check Aborted Automations**
   ```bash
   ls -la automation_state/
   # Remove any stale state files if needed
   ```

4. **Restart Service**
   ```bash
   sudo systemctl restart siya
   ```

---

### 2. Database Corruption Recovery

**Symptoms:**
- Database errors in logs
- State consistency check fails
- SQLite errors

**Recovery Steps:**

1. **Backup Current Database**
   ```bash
   cp siya.db siya.db.backup.$(date +%Y%m%d_%H%M%S)
   ```

2. **Check Database Integrity**
   ```bash
   sqlite3 siya.db "PRAGMA integrity_check;"
   ```

3. **Run State Recovery**
   ```bash
   python -c "
   from memory import Database
   from system import StateChecker
   db = Database('siya.db')
   db.connect()
   checker = StateChecker(db)
   result = checker.check_state_consistency()
   if result['issues']:
       checker.recover_state(result['issues'])
   "
   ```

4. **If Recovery Fails:**
   - Restore from backup
   - Or recreate database (data loss)

---

### 3. AI Model Crash Recovery

**Symptoms:**
- Intent parsing fails
- AI model errors in logs
- High/CRITICAL failures logged

**Recovery Steps:**

1. **Check Failure Logs**
   ```bash
   sudo journalctl -u siya | grep "AI_CRASH"
   ```

2. **Restart AI Model**
   ```bash
   # AI model will be reloaded on next intent parsing request
   # Or restart service
   sudo systemctl restart siya
   ```

3. **Verify Recovery**
   ```bash
   # Test intent parsing
   curl -X POST http://localhost:8080/command \
     -H "Content-Type: application/json" \
     -d '{"command": "test"}'
   ```

---

### 4. Resource Exhaustion Recovery

**Symptoms:**
- High RAM/CPU/disk usage
- System slow or unresponsive
- Resource exhaustion failures logged

**Recovery Steps:**

1. **Check Resource Usage**
   ```bash
   python -c "
   from system import ResourceMonitor
   monitor = ResourceMonitor()
   status = monitor.check_resources()
   print(f'RAM: {status[\"ram_usage\"]*100:.1f}%')
   print(f'CPU: {status[\"cpu_usage\"]*100:.1f}%')
   print(f'Disk: {status[\"disk_usage\"]*100:.1f}%')
   "
   ```

2. **Free Resources**
   ```bash
   # Clear old logs
   sudo journalctl --vacuum-time=7d
   
   # Clear old automation state
   find automation_state/ -name "*.json" -mtime +7 -delete
   
   # Check disk space
   df -h
   ```

3. **Restart Service**
   ```bash
   sudo systemctl restart siya
   ```

---

### 5. Network Loss Recovery

**Symptoms:**
- Network connectivity lost
- Offline mode active
- Network loss failures logged

**Recovery Steps:**

1. **Check Network Status**
   ```bash
   ping -c 3 8.8.8.8
   ```

2. **Restart Network (if needed)**
   ```bash
   sudo systemctl restart networking
   ```

3. **Verify Recovery**
   ```bash
   # System should automatically detect network restoration
   # Check logs for network recovery
   sudo journalctl -u siya | grep "NETWORK"
   ```

---

### 6. Complete System Recovery

**Symptoms:**
- System completely unresponsive
- Multiple failures
- Unknown state

**Recovery Steps:**

1. **Stop Service**
   ```bash
   sudo systemctl stop siya
   ```

2. **Backup Current State**
   ```bash
   tar -czf siya_recovery_$(date +%Y%m%d_%H%M%S).tar.gz \
     siya.db \
     automation_state/ \
     production_lock.json
   ```

3. **Run Full State Check**
   ```bash
   python -c "
   from memory import Database
   from system import StateChecker
   db = Database('siya.db')
   db.connect()
   checker = StateChecker(db)
   result = checker.check_state_consistency()
   print(f'Consistent: {result[\"consistent\"]}')
   print(f'Issues: {result[\"issues\"]}')
   if result['issues']:
       checker.recover_state(result['issues'])
   "
   ```

4. **Clear Stale State**
   ```bash
   rm -f automation_state/*.json
   ```

5. **Restart Service**
   ```bash
   sudo systemctl start siya
   ```

6. **Verify System**
   ```bash
   # Check service status
   sudo systemctl status siya
   
   # Check API health
   curl http://localhost:8080/health
   
   # Check logs
   sudo journalctl -u siya -f
   ```

---

## PREVENTION

### Regular Maintenance

1. **Daily:**
   - Monitor logs: `sudo journalctl -u siya --since today`
   - Check resource usage

2. **Weekly:**
   - Run state consistency check
   - Review audit logs
   - Clean old automation state

3. **Monthly:**
   - Database backup
   - System update (if needed)
   - Review failure patterns

---

## BACKUP PROCEDURES

### Database Backup

```bash
# Create backup
cp siya.db siya.db.backup.$(date +%Y%m%d)

# Or use SQLite backup
sqlite3 siya.db ".backup siya.db.backup"
```

### Full System Backup

```bash
tar -czf siya_backup_$(date +%Y%m%d).tar.gz \
  siya.db \
  automation_state/ \
  production_lock.json \
  venv/ \
  *.py
```

---

## CONTACT & SUPPORT

For issues not covered in this checklist:
1. Check logs: `sudo journalctl -u siya`
2. Review audit logs in database
3. Check system documentation

---

**Last Updated:** 2026-01-26
**Baseline Version:** 1.0.0
