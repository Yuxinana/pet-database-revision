import re

with open("pawtrack_demo.html", "r") as f:
    content = f.read()

# 1. Enhance empty state in renderTableRows
old_empty_state = """    : `<tr><td colspan="${colspan}" style="text-align:center;padding:2rem;color:var(--color-text-secondary)">No data found</td></tr>`;"""
new_empty_state = """    : `<tr><td colspan="${colspan}" style="text-align:center;padding:3rem 1rem;">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" style="opacity:0.4; margin-bottom:12px; color:var(--color-primary)">
          <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"></path>
          <polyline points="3.27 6.96 12 12.01 20.73 6.96"></polyline>
          <line x1="12" y1="22.08" x2="12" y2="12"></line>
        </svg>
        <div style="font-size:15px;font-weight:600;color:var(--color-text-secondary);margin-bottom:4px">No records found</div>
        <div style="font-size:13px;color:var(--color-text-tertiary)">It looks like there is no data to display here at the moment.</div>
      </td></tr>`;"""
content = content.replace(old_empty_state, new_empty_state)

# 2. Add visual icons to Medical page titles
old_medical_visits_title = """<span class="section-title">Medical visits</span>"""
new_medical_visits_title = """<span class="section-title" style="display:flex;align-items:center;gap:8px">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-info)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M22 12h-4l-3 9L9 3l-3 9H2"></path></svg>
          Medical visits
        </span>"""
content = content.replace(old_medical_visits_title, new_medical_visits_title)

old_vaccinations_title = """<span class="section-title">Vaccinations</span>"""
new_vaccinations_title = """<span class="section-title" style="display:flex;align-items:center;gap:8px">
          <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--color-text-success)" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M14 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8z"></path><polyline points="14 2 14 8 20 8"></polyline><line x1="16" y1="13" x2="8" y2="13"></line><line x1="16" y1="17" x2="8" y2="17"></line><polyline points="10 9 9 9 8 9"></polyline></svg>
          Vaccinations
        </span>"""
content = content.replace(old_vaccinations_title, new_vaccinations_title)

# Add a decorative header to the page titles (global)
old_page_title = """<div class="page-title">"""
new_page_title = """<div class="page-title" style="display:flex; align-items:center; gap:12px;">"""
content = content.replace(old_page_title, new_page_title)

# Replace specific "No ... found" with the nice empty state for manually rendered tables (pets, apps, medical, etc.)
def replace_empty_tr(match):
    colspan = match.group(1)
    text = match.group(2)
    return f"""'`<tr><td colspan="{colspan}" style="text-align:center;padding:3rem 1rem;">
        <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.2" stroke-linecap="round" stroke-linejoin="round" style="opacity:0.4; margin-bottom:12px; color:var(--color-primary)">
          <circle cx="12" cy="12" r="10"></circle><path d="M16 16s-1.5-2-4-2-4 2-4 2"></path><line x1="9" y1="9" x2="9.01" y2="9"></line><line x1="15" y1="9" x2="15.01" y2="9"></line>
        </svg>
        <div style="font-size:15px;font-weight:600;color:var(--color-text-secondary);margin-bottom:4px">No {text.lower()}</div>
        <div style="font-size:13px;color:var(--color-text-tertiary)">We couldn\\'t find any {text.lower()} matching your criteria.</div>
      </td></tr>`'"""

content = re.sub(r"\'<tr><td colspan=\"(\d+)\" style=\"text-align:center;padding:2rem;color:var\(--color-text-secondary\)\">No ([^<]+) found</td></tr>\'", replace_empty_tr, content)

# 3. Dashboard visual enhancements
# Enhance stat cards on Dashboard
content = content.replace(
    '<div class="stat-label">Total pets</div>',
    '<div class="stat-label" style="display:flex;align-items:center;justify-content:space-between"><span>Total pets</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="opacity:0.5"><circle cx="12" cy="12" r="10"></circle><path d="M8 14s1.5 2 4 2 4-2 4-2"></path><line x1="9" y1="9" x2="9.01" y2="9"></line><line x1="15" y1="9" x2="15.01" y2="9"></line></svg></div>'
)

content = content.replace(
    '<div class="stat-label">Available now</div>',
    '<div class="stat-label" style="display:flex;align-items:center;justify-content:space-between;color:#3B6D11"><span>Available now</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="opacity:0.5"><path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"></path><polyline points="22 4 12 14.01 9 11.01"></polyline></svg></div>'
)

content = content.replace(
    '<div class="stat-label">Pending review</div>',
    '<div class="stat-label" style="display:flex;align-items:center;justify-content:space-between;color:#854F0B"><span>Pending review</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="opacity:0.5"><circle cx="12" cy="12" r="10"></circle><polyline points="12 6 12 12 16 14"></polyline></svg></div>'
)

content = content.replace(
    '<div class="stat-label">This month</div>',
    '<div class="stat-label" style="display:flex;align-items:center;justify-content:space-between;color:#185FA5"><span>This month adoptions</span><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="opacity:0.5"><path d="M14 9V5a3 3 0 0 0-3-3l-4 9v11h11.28a2 2 0 0 0 2-1.7l1.38-9a2 2 0 0 0-2-2.3zM7 22H4a2 2 0 0 1-2-2v-7a2 2 0 0 1 2-2h3"></path></svg></div>'
)

# Fix missing title for dashboard
content = content.replace(
    '<div class="page-title" style="display:flex; align-items:center; gap:12px;">Dashboard</div>',
    '<div class="page-title" style="display:flex; align-items:center; gap:12px;"><div style="width:40px;height:40px;background:var(--color-primary-light);border-radius:10px;display:flex;align-items:center;justify-content:center;color:var(--color-primary);"><svg width="24" height="24" viewBox="0 0 16 16" fill="none" stroke="currentColor" stroke-width="1.2"><rect x="1" y="1" width="6" height="6" rx="1"/><rect x="9" y="1" width="6" height="6" rx="1"/><rect x="1" y="9" width="6" height="6" rx="1"/><rect x="9" y="9" width="6" height="6" rx="1"/></svg></div>Dashboard</div>'
)

with open("pawtrack_demo.html", "w") as f:
    f.write(content)
