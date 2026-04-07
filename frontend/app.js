document.addEventListener("DOMContentLoaded", () => {
    const rawQueryInput = document.getElementById("raw-query");
    const btnEnhance = document.getElementById("btn-enhance");
    const loader1 = document.getElementById("loader-1");

    const step2 = document.getElementById("step-2");
    const optionsGrid = document.getElementById("query-options");
    const selectedQueryInput = document.getElementById("selected-query");
    const btnSearch = document.getElementById("btn-search");
    const loader2 = document.getElementById("loader-2");

    const step3 = document.getElementById("step-3");
    const papersGrid = document.getElementById("papers-list");
    const btnSummarize = document.getElementById("btn-summarize");
    const loader3 = document.getElementById("loader-3");

    const step4 = document.getElementById("step-4");
    const resultsContainer = document.getElementById("results-container");

    let currentPapers = [];
    let selectedPaperIds = new Set();

    function showLoader(loader) { loader.classList.remove("hidden"); }
    function hideLoader(loader) { loader.classList.add("hidden"); }
    function revealElement(el) { el.classList.remove("hidden"); el.classList.remove("compacted"); }

    rawQueryInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            btnEnhance.click();
        }
    });

    btnEnhance.addEventListener("click", async () => {
        const query = rawQueryInput.value.trim();
        if (!query) return;

        btnEnhance.disabled = true;
        showLoader(loader1);

        try {
            const res = await fetch("/api/enhance", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query })
            });

            if (!res.ok) throw new Error("Enhancement failed");
            const data = await res.json();
            
            const variants = Array.from(new Set([query, ...data.variants]));
            optionsGrid.innerHTML = "";
            variants.forEach((v, index) => {
                const card = document.createElement("div");
                card.className = "radio-card" + (index === 1 ? " selected" : "");
                card.innerText = v;
                card.addEventListener("click", () => {
                    document.querySelectorAll(".radio-card").forEach(c => c.classList.remove("selected"));
                    card.classList.add("selected");
                    selectedQueryInput.value = v;
                });
                optionsGrid.appendChild(card);
                if (index === 1 || (index === 0 && variants.length === 1)) {
                    selectedQueryInput.value = v;
                }
            });

            hideLoader(loader1);
            btnEnhance.disabled = false;
            revealElement(step2);
            setTimeout(() => step2.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);

        } catch (err) {
            console.error(err);
            alert("Error connecting to API. Is the fastAPI server running?");
            hideLoader(loader1);
            btnEnhance.disabled = false;
        }
    });

    selectedQueryInput.addEventListener("keydown", (e) => {
        if (e.key === "Enter") {
            e.preventDefault();
            btnSearch.click();
        }
    });

    btnSearch.addEventListener("click", async () => {
        const query = selectedQueryInput.value.trim();
        if (!query) return;

        btnSearch.disabled = true;
        showLoader(loader2);

        try {
            const res = await fetch("/api/search", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ query })
            });
            if (!res.ok) throw new Error("Search failed");
            const data = await res.json();
            currentPapers = data.papers;
            selectedPaperIds.clear();

            papersGrid.innerHTML = "";
            if (currentPapers.length === 0) {
                papersGrid.innerHTML = "<p>No papers found on arXiv for this query.</p>";
            } else {
                currentPapers.forEach(paper => {
                    const div = document.createElement("div");
                    div.className = "paper-item";
                    div.innerHTML = `
                        <div class="paper-checkbox"></div>
                        <div class="paper-content">
                            <h3>${paper.title}</h3>
                            <div class="paper-meta">👤 ${paper.authors.length > 70 ? paper.authors.substring(0,70)+'...' : paper.authors} <br> 📅 ${paper.year} • 🏷️ ${paper.categories.slice(0,2).join(', ')} • 🔗 <a href="${paper.html_url}" target="_blank">PDF</a></div>
                        </div>
                    `;
                    div.addEventListener("click", () => {
                        div.classList.toggle("selected");
                        if (div.classList.contains("selected")) selectedPaperIds.add(paper.arxiv_id);
                        else selectedPaperIds.delete(paper.arxiv_id);
                    });
                    papersGrid.appendChild(div);
                });
            }

            hideLoader(loader2);
            btnSearch.disabled = false;
            revealElement(step3);
            setTimeout(() => step3.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);

        } catch (err) {
            console.error(err);
            hideLoader(loader2);
            btnSearch.disabled = false;
            alert("Failed to search arXiv.");
        }
    });

    btnSummarize.addEventListener("click", async () => {
        if (selectedPaperIds.size === 0) {
            alert("Please select at least one paper.");
            return;
        }

        const selectedPapers = currentPapers.filter(p => selectedPaperIds.has(p.arxiv_id));
        
        btnSummarize.disabled = true;
        showLoader(loader3);

        try {
            const res = await fetch("/api/summarize", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ papers: selectedPapers })
            });

            if(!res.ok) {
                const text = await res.text();
                throw new Error("Summarization failed: " + text);
            }
            const data = await res.json();

            resultsContainer.innerHTML = "";
            let allFeatures = [];
            
            data.summaries.forEach(s => {
                const card = document.createElement("div");
                card.className = "result-card";
                
                const tags = `<span class="tag">ID: ${s.arxiv_id}</span><span class="tag">${s.year}</span>`;
                allFeatures.push(s);
                
                // Construct the features table
                const fData = [
                    { k: "Comprehensive Summary", v: s.summary },
                    { k: "Research Problem & Gap", v: (s.research_problem + "<br><br><b>Gap:</b> " + s.research_gap_addressed).replace(/N\/A — not reported/g,'') },
                    { k: "Proposed Method", v: s.proposed_method },
                    { k: "Results & Metrics", v: s.results_performance === "N/A — not reported" ? s.evaluation_metrics : s.results_performance },
                    { k: "Limitations & Future", v: (s.limitations + "<br><br><b>Future:</b> " + s.future_work).replace(/N\/A — not reported/g,'') },
                    { k: "Code / Repo", v: s.code_repo }
                ];
                
                let tbodyRows = "";
                fData.forEach(f => {
                    let val = f.v;
                    if (!val || val === "N/A — not reported" || val.replace(/<[^>]*>?/gm, '').trim() === "") {
                        val = `<span class="na">Not extracted or N/A in this paper</span>`;
                    }
                    tbodyRows += `<tr><th>${f.k}</th><td>${val}</td></tr>`;
                });

                card.innerHTML = `
                    <div class="result-header">
                        <h3>${s.paper_title || "Unknown Title"}</h3>
                        <div class="paper-meta">👤 ${s.authors}</div>
                        <div class="result-tags">${tags}</div>
                    </div>
                    <div class="result-body-table-wrapper">
                        <table class="glass-table">
                            <tbody>${tbodyRows}</tbody>
                        </table>
                    </div>
                `;
                resultsContainer.appendChild(card);
            });

            // ADD COMBINED MATRIX
            const matrixDiv = document.createElement("div");
            matrixDiv.className = "matrix-card hidden-mobile";
            
            // All 18 features!
            const columns = [
                "paper_title", "authors", "year", "arxiv_id", "summary", 
                "research_problem", "proposed_method", "key_contributions", 
                "dataset_used", "evaluation_metrics", "results_performance", 
                "limitations", "future_work", "research_gap_addressed", 
                "remaining_gaps", "related_work_referenced", "code_repo", "applicability"
            ];
            
            let mHead = columns.map(c => `<th>${c.replace(/_/g, ' ')}</th>`).join('');
            let mBody = allFeatures.map(f => {
                return `<tr>${columns.map(c => {
                    let val = f[c];
                    if (!val || val === "N/A — not reported") val = `<span class="na">N/A</span>`;
                    return `<td><div class="scroll-cell">${val}</div></td>`;
                }).join('')}</tr>`;
            }).join('');
            
            matrixDiv.innerHTML = `
                <div class="result-header" style="border-bottom:none"><h3>Combined Comparison Matrix</h3></div>
                <div class="table-responsive">
                    <table class="glass-table matrix-table">
                        <thead><tr>${mHead}</tr></thead>
                        <tbody>${mBody}</tbody>
                    </table>
                </div>
                
                <div class="export-actions">
                    <button id="btn-export-csv" class="stellar-button primary">⬇️ Download CSV</button>
                    <button id="btn-export-md" class="stellar-button" style="background:rgba(255,255,255,0.1); border:1px solid rgba(255,255,255,0.2); color:white;">⬇️ Download Markdown</button>
                </div>
            `;
            resultsContainer.appendChild(matrixDiv);
            
            // Hook up exports
            document.getElementById("btn-export-csv").addEventListener("click", () => triggerExport("/api/export/csv", allFeatures, "research_summary.csv"));
            document.getElementById("btn-export-md").addEventListener("click", () => triggerExport("/api/export/markdown", allFeatures, "research_summary.md"));

            hideLoader(loader3);
            btnSummarize.disabled = false;
            revealElement(step4);
            setTimeout(() => step4.scrollIntoView({ behavior: 'smooth', block: 'start' }), 100);

        } catch (err) {
            console.error(err);
            hideLoader(loader3);
            btnSummarize.disabled = false;
            alert(err.message || "Failed to extract data. See console.");
        }
    });

    async function triggerExport(endpoint, summaries, filename) {
        try {
            const res = await fetch(endpoint, {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ summaries })
            });
            if (!res.ok) throw new Error("Export failed");
            
            const blob = await res.blob();
            const url = window.URL.createObjectURL(blob);
            const a = document.createElement("a");
            a.style.display = "none";
            a.href = url;
            a.download = filename;
            document.body.appendChild(a);
            a.click();
            window.URL.revokeObjectURL(url);
        } catch (e) {
            alert("Error exporting: " + e.message);
        }
    }

});
