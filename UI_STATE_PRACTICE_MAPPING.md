# UI Enhancement: State/Practice Mapping & Statistics

**Implemented:** October 28, 2025  
**Status:** ✅ Complete

---

## 🎯 What Was Built

Enhanced the Medical ETL Review Queue UI to show **multi-practice statistics** with state/practice breakdown, scan counts, and copy rates.

---

## 📊 New Dashboard Stats

### **Top Stat Cards (6 widgets)**

| Card | Description | Color |
|------|-------------|-------|
| **States** | Unique state count (e.g., TX, CA, NC) | Cyan |
| **Practices** | Unique practice count | Blue |
| **Scanned** | Total files processed from source | Black |
| **Copied** | Files successfully copied to destination | Green |
| **Unmapped** | Files that couldn't be matched to patients | Yellow |
| **Errors** | Files with processing errors | Red |

---

## 📈 New "Practices" Tab

**Default tab showing practice breakdown:**

| Column | Description |
|--------|-------------|
| **State** | State code (TX, CA, NC, etc.) |
| **Practice** | Practice name (Alexander_OBGYN, Triangle_ENT, etc.) |
| **Scanned** | Files scanned from source |
| **Copied** | Files copied to destination |
| **Unmapped** | Files that couldn't be matched |
| **Errors** | Files with processing errors |
| **Copy Rate** | Visual progress bar showing copy success rate |

**Copy Rate Color Coding:**
- 🟢 Green: ≥80% (excellent)
- 🟡 Yellow: 50-79% (needs attention)
- 🔴 Red: <50% (critical - likely roster issue)

---

## 🔧 Technical Implementation

### 1. Path Parsing Logic

**Function:** `parse_state_practice_from_path(path)`

**Input Path Example:**
```
\\mrm-fileserver\practice records\TX\Alexander_OBGYN\Export\Labs\Smith_John.pdf
```

**Parsing Logic:**
1. Search for "practice records" folder in path
2. Extract next level = State (e.g., "TX")
3. Extract next level = Practice (e.g., "Alexander_OBGYN")

**Output:**
```python
state = "TX"
practice = "Alexander_OBGYN"
```

**Handles variations:**
- Windows UNC paths: `\\server\path`
- Unix paths: `/server/path`
- Mixed slashes: `\\server/path`

---

### 2. API Endpoints

#### **GET /api/stats**

**Enhanced to include state/practice counts:**

```json
{
  "states": 3,           // Unique states (TX, CA, NC)
  "practices": 5,        // Unique practices
  "total_files": 150,    // Total scanned
  "copied": 120,         // Successfully copied
  "unmapped": 25,        // Unmapped files
  "errors": 5            // Processing errors
}
```

**Implementation:**
- Queries all distinct `SourcePath` values from `FACT_FileProcessing`
- Parses state/practice from each path
- Counts unique states and practices using sets

---

#### **GET /api/practice-stats**

**Returns practice breakdown array:**

```json
[
  {
    "state": "TX",
    "practice": "Alexander_OBGYN",
    "scanned": 50,
    "copied": 45,
    "unmapped": 5,
    "errors": 0
  },
  {
    "state": "CA",
    "practice": "Valley_Neurology",
    "scanned": 80,
    "copied": 70,
    "unmapped": 8,
    "errors": 2
  },
  {
    "state": "NC",
    "practice": "Triangle_ENT",
    "scanned": 20,
    "copied": 5,
    "unmapped": 12,
    "errors": 3
  }
]
```

**Sorting:** Results sorted by state, then practice name

---

### 3. UI Auto-Refresh

**Refresh Intervals:**
- Stats cards: Every 30 seconds
- Practice breakdown: Every 30 seconds
- Recent runs: On tab click
- Unmapped files: On tab click

**Implementation:**
```javascript
setInterval(loadStats, 30000);
setInterval(loadPractices, 30000);
```

---

## 📸 Screenshot

**Dashboard shows:**
- 6 stat cards at top: States, Practices, Scanned, Copied, Unmapped, Errors
- "Practices" tab as default view
- Practice breakdown table with state badges, practice names, statistics, and copy rate progress bars
- Color-coded progress bars showing copy success rate

---

## 🔍 Example Use Cases

### **Use Case 1: Multi-Practice Health Check**

**Question:** How are all practices performing?

**Answer:** Check the "Practices" tab
- See each practice's scan/copy/unmapped/error counts
- Copy rate progress bars show which practices need attention
- Red bars (< 50%) indicate likely roster issues

---

### **Use Case 2: State-Level Reporting**

**Question:** How many states and practices are we processing?

**Answer:** Top stat cards show:
- States: 3 (TX, CA, NC)
- Practices: 5 (across all states)

---

### **Use Case 3: Identify Problem Practices**

**Question:** Which practice has the highest unmapped rate?

**Answer:** Sort practice table by copy rate:
- Triangle_ENT: 25% copy rate (RED) - 12/20 unmapped
- Alexander_OBGYN: 90% copy rate (GREEN) - 5/50 unmapped
- Valley_Neurology: 87% copy rate (GREEN) - 8/80 unmapped

**Action:** Investigate Triangle_ENT's roster configuration

---

## 🚀 Real-World Example

**Scenario:** Processing files from 3 practices

**Source Paths:**
```
\\mrm-fileserver\practice records\TX\Alexander_OBGYN\Export\file1.pdf
\\mrm-fileserver\practice records\CA\Valley_Neurology\Export\file2.pdf
\\mrm-fileserver\practice records\NC\Triangle_ENT\Export\file3.pdf
```

**Dashboard Shows:**
- **States:** 3 (TX, CA, NC)
- **Practices:** 3 (Alexander_OBGYN, Valley_Neurology, Triangle_ENT)
- **Scanned:** 150 total files
- **Copied:** 120 successfully copied
- **Unmapped:** 25 couldn't be matched
- **Errors:** 5 processing errors

**Practice Breakdown Table:**

| State | Practice | Scanned | Copied | Unmapped | Errors | Copy Rate |
|-------|----------|---------|--------|----------|--------|-----------|
| CA | Valley_Neurology | 80 | 70 | 8 | 2 | 🟢 87% |
| NC | Triangle_ENT | 20 | 5 | 12 | 3 | 🔴 25% |
| TX | Alexander_OBGYN | 50 | 45 | 5 | 0 | 🟢 90% |

**Insight:** Triangle_ENT has 25% copy rate (RED) - likely roster issue. Check roster configuration!

---

## 🎯 Benefits

### **Before:**
- ❌ No visibility into state/practice breakdown
- ❌ Couldn't see which practices were performing well
- ❌ No way to identify problem practices quickly
- ❌ Manual query needed to count states/practices

### **After:**
- ✅ Real-time state/practice stats at a glance
- ✅ Color-coded copy rates for quick health check
- ✅ Sortable table to identify problem practices
- ✅ Auto-refreshing every 30 seconds
- ✅ Visual progress bars showing copy success rate

---

## 🔄 Data Flow

```
FACT_FileProcessing Table
  └─> SELECT DISTINCT SourcePath
      └─> Parse each path for state/practice
          └─> Group by state|practice key
              └─> Aggregate statistics (scanned, copied, unmapped, errors)
                  └─> Return sorted array to UI
                      └─> Render table with progress bars
```

---

## 📁 Files Modified

| File | Changes |
|------|---------|
| `review_ui/app.py` | Added `parse_state_practice_from_path()`, updated `/api/stats`, added `/api/practice-stats` |
| `review_ui/templates/index.html` | Added 6 stat cards, new "Practices" tab, loadPractices() function, auto-refresh |

---

## 🧪 Testing

**Test Path Parsing:**
```python
parse_state_practice_from_path("\\mrm-fileserver\\practice records\\TX\\Alexander_OBGYN\\Export\\file.pdf")
# Returns: ("TX", "Alexander_OBGYN")

parse_state_practice_from_path("//server/practice records/CA/Valley_Neurology/file.pdf")
# Returns: ("CA", "Valley_Neurology")
```

**Test API Endpoints:**
```bash
# Get overall stats
curl http://localhost:5000/api/stats

# Get practice breakdown
curl http://localhost:5000/api/practice-stats
```

---

## 💡 Future Enhancements

**Performance Optimization:**
- Cache state/practice parsing results
- Add database columns for state/practice (avoid parsing on every query)
- Pre-compute statistics in background job

**UI Improvements:**
- Click state/practice to filter files
- Export practice breakdown to CSV
- Add date range filter
- Show trend graphs (copy rate over time)

**Analytics:**
- Average copy rate across all practices
- Identify practices with declining copy rates
- Alert when practice copy rate drops below threshold

---

## 📚 Related Documentation

- `BRONZE_SILVER_GOLD_ARCHITECTURE.md` - Multi-practice warehouse architecture
- `DETAILED_FLOWCHARTS.md` - Processing pipeline flowcharts
- `QUICK_WINS_IMPLEMENTED.md` - Validation and autodetect features

---

**Ready to Use!** 🚀

The UI now provides complete visibility into multi-practice ETL processing with real-time statistics and performance monitoring.
