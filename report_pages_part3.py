# Pages 15 to 21 of the Technical Audit Report

def get_page_15():
    return """
    <h1>Chapter 7: Conversational BI & NL-to-SQL Engine</h1>
    <h2>7.1 Translating Natural Language to Columnar SQL</h2>
    <p>The conversational Q&A capability in DataMind AI operates through the <span class="mono">AnalystAgent</span>. Unlike basic chat wrappers that feed tabular data directly into LLM prompts (often hitting token limits and hallucinating metrics), DataMind AI uses an intent-driven SQL generation pipeline:</p>

    <div class="diagram-box">
Natural Language Input: "Which product line yielded the greatest profit margin in Europe?"
   │
   ├─► Step 1: Language & Script Classification (English, Hindi Devanagari, Hinglish, Spanish)
   │
   ├─► Step 2: Metric & Dimension Entity Disambiguation
   │           &bull; "product line"   ──► Mapped to column: "Product"
   │           &bull; "profit margin"  ──► Mapped to formula: "SUM(Profit) / SUM(Revenue)"
   │           &bull; "Europe"         ──► Identified as categorical filter on "Region"
   │           &bull; "greatest"       ──► Order By DESC + LIMIT 1
   │
   ├─► Step 3: Deterministic SQL Synthesis
   │           SELECT "Product", ROUND(SUM("Profit")*100.0/SUM("Revenue"), 2) AS margin_pct
   │           FROM dataset WHERE "Region" = 'Europe' GROUP BY "Product" ORDER BY margin_pct DESC LIMIT 5;
   │
   ├─► Step 4: DuckDB Execution on In-Memory Parquet View (< 12 ms)
   │
   └─► Step 5: Verified Synthesis Node -> Generates Human Narrative & ECharts Visual Spec
    </div>

    <h2>7.2 Domain Synonym & Business Dictionary Mapping</h2>
    <p>A core architectural asset of the platform is its extensive built-in synonym mapping matrix (<span class="mono">AnalystAgent.MEASURE_SYNONYMS</span> and <span class="mono">DIMENSION_SYNONYMS</span>). This layer decouples user vocabulary from literal database column identifiers:</p>

    <table class="tech-table">
        <thead>
            <tr>
                <th>User Keyword Concept</th>
                <th>Multilingual Synonyms Supported</th>
                <th>Mapped Physical Database Attribute</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>Revenue / Sales</strong></td>
                <td><span class="mono">turnover, sales, gross, bikri, kamai, ingresos, ventas</span></td>
                <td><span class="mono">sales_inr, gross_sales_inr, revenue</span></td>
            </tr>
            <tr>
                <td><strong>Profit / Return</strong></td>
                <td><span class="mono">margin, net profit, munafa, fayda, ganancia, margen</span></td>
                <td><span class="mono">profit_inr, profit_margin_pct, profit</span></td>
            </tr>
            <tr>
                <td><strong>Cost / Expense</strong></td>
                <td><span class="mono">expense, spending, kharcha, costo, gasto</span></td>
                <td><span class="mono">cost_inr, cost, expense, treatment_cost</span></td>
            </tr>
            <tr>
                <td><strong>Geography / Zone</strong></td>
                <td><span class="mono">state, city, shehar, rajya, zone, region, division, area</span></td>
                <td><span class="mono">region, state, division, city</span></td>
            </tr>
            <tr>
                <td><strong>Quantity / Volume</strong></td>
                <td><span class="mono">units, count, ginti, volumen, cantidad</span></td>
                <td><span class="mono">quantity, volume, order_count</span></td>
            </tr>
        </tbody>
    </table>
    """

def get_page_16():
    return """
    <h1>Chapter 7.2: Zero-Hallucination Verification Pipeline</h1>
    <h2>7.3 The Flaw of LLM-Calculated Statistics</h2>
    <p>Large Language Models are probabilistic next-token predictors. When asked to perform aggregations over thousands of rows (e.g. <em>"What was our net margin in Q3?"</em>), an LLM without code-execution grounding will generate plausible-sounding but mathematically fabricated numbers. In an enterprise financial or healthcare environment, acting on hallucinated analytics can lead to catastrophic business decisions.</p>

    <h2>7.4 The DataMind AI Zero-Trust Calculation Protocol</h2>
    <p>To eliminate calculation error entirely, DataMind AI enforces a strict architectural boundary: <strong>The LLM is forbidden from calculating numbers directly.</strong></p>

    <div class="grid-2">
        <div class="callout callout-tech">
            <strong>1. Deterministic Execution Isolation:</strong>
            <br>All mathematical aggregations (<span class="mono">SUM, AVG, MEDIAN, STDDEV, COUNT</span>), filter conditions, and group-by projections execute strictly within the C++ kernels of DuckDB. The returned result set is verified against physical row structures.
        </div>
        <div class="callout callout-insight">
            <strong>2. Evidence-Grounded Synthesis:</strong>
            <br>The Analyst Agent's explanatory generator is provided with the verified tabular output as an immutable ground truth. The agent's role is restricted to translating verified database facts into clean, professional narrative prose.
        </div>
    </div>

    <h2>7.5 Fallback Semantic Planner: 100% Offline Resilience</h2>
    <p>While DataMind AI supports external state-of-the-art LLMs (Groq LLaMA-3.3-70B, OpenAI GPT-4o, Google Gemini 2.0 Pro), it does not depend on them to function. If no external API keys are configured, or if corporate networks operate in air-gapped isolation, an internal <strong>Deterministic Semantic Planner</strong> takes over automatically:</p>

    <div class="code-snippet">
# Built-in offline semantic planner logic in AIAgent & AnalystAgent
if not sql_query:
    sql_query, detected_intent = AIAgent._generate_sql_rule_based(q_lower, profile, user_lang)
    # Automatically extracts target measure, slicing dimension, time filters,
    # and aggregation mode ('top', 'bottom', 'total', 'average', 'distribution')
    </div>

    <p>This ensures the platform maintains 100% operational readiness out-of-the-box in any enterprise network deployment.</p>
    """

def get_page_17():
    return """
    <h1>Chapter 7.3: Multilingual Analytical NLP in Practice</h1>
    <h2>7.6 Language Identification & Morphological Analysis</h2>
    <p>DataMind AI features a built-in multilingual engine capable of detecting and responding in English, Hindi (Devanagari script), Romanized Hinglish, and Spanish. Detection operates via character set analysis and lexical matching:</p>

    <div class="code-snippet">
def detect_language(text: str) -> str:
    # 1. Unicode Range Probe: Hindi Devanagari script (U+0900 to U+097F)
    if re.search(r"[\u0900-\u097F]", text): return "hi_devanagari"
    # 2. Lexical Token Probe: Romanized Hinglish business vernacular
    hinglish_tokens = ["kaunsa", "kisme", "kitna", "sabse", "jyada", "zyada", "kam", 
                       "batao", "dikhao", "bikri", "kamai", "munafa", "shikayat", "rajya"]
    if any(re.search(rf"\\b{w}\\b", text.lower()) for w in hinglish_tokens): return "hi_hinglish"
    # 3. Lexical Token Probe: Spanish business terminology
    spanish_tokens = ["cuál", "cuánto", "ingresos", "ventas", "más", "promedio"]
    if any(re.search(rf"\\b{w}\\b", text.lower()) for w in spanish_tokens): return "es"
    return "en"
    </div>

    <h2>7.7 Comparative Execution Traces Across Languages</h2>
    <p>Below are three verified execution traces demonstrating how the same analytical intent is parsed across different linguistic inputs:</p>

    <table class="tech-table">
        <thead>
            <tr><th>Language</th><th>User Prompt</th><th>Compiled Deterministic SQL</th><th>Localized Agent Explanation</th></tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>English</strong></td>
                <td><em>"Which region generated the highest revenue?"</em></td>
                <td class="mono">SELECT "Region", SUM("Revenue") AS v FROM dataset GROUP BY 1 ORDER BY 2 DESC LIMIT 5;</td>
                <td><strong>North America</strong> leads all regions with a total revenue of <strong>$4.82M</strong>, representing 28.6% of overall sales volume.</td>
            </tr>
            <tr>
                <td><strong>Hinglish</strong></td>
                <td><em>"Sabse jyada bikri kaunse region me hui hai?"</em></td>
                <td class="mono">SELECT "Region", SUM("Revenue") AS v FROM dataset GROUP BY 1 ORDER BY 2 DESC LIMIT 5;</td>
                <td>Sabse zyada bikri <strong>North America</strong> me darj hui hai, jahan kul revenue <strong>$4.82M</strong> raha (kul bikri ka 28.6%).</td>
            </tr>
            <tr>
                <td><strong>Hindi (Devanagari)</strong></td>
                <td><em>"सबसे अधिक राजस्व किस क्षेत्र से प्राप्त हुआ है?"</em></td>
                <td class="mono">SELECT "Region", SUM("Revenue") AS v FROM dataset GROUP BY 1 ORDER BY 2 DESC LIMIT 5;</td>
                <td>सबसे अधिक राजस्व <strong>North America</strong> क्षेत्र से प्राप्त हुआ है, जहाँ कुल <strong>$4.82M</strong> की बिक्री दर्ज की गई।</td>
            </tr>
        </tbody>
    </table>
    """

def get_page_18():
    return """
    <h1>Chapter 8: Automated AI Insights & Discovery</h1>
    <h2>8.1 The Automated Discovery Imperative</h2>
    <p>Business users frequently do not know what questions to ask when confronting an unfamiliar dataset. Relying solely on manual query interfaces leaves critical correlations, hidden anomalies, and segment concentrations undetected. The <span class="mono">InsightsEngine</span> executes an autonomous statistical exploration sweep across all dataset dimensions, surfacing high-value patterns without prompting.</p>

    <h2>8.2 Multi-Variable Pearson Correlation Matrix</h2>
    <p>The engine queries pairwise correlations across all continuous measures using DuckDB's native SIMD-accelerated <span class="mono">corr(X, Y)</span> function:</p>

    <div class="callout callout-tech">
        <strong>Pearson Product-Moment Correlation Coefficient Formulation:</strong>
        <br>$$r_{XY} = \frac{\sum_{i=1}^{n}(X_i - \bar{X})(Y_i - \bar{Y})}{\sqrt{\sum_{i=1}^{n}(X_i - \bar{X})^2}\sqrt{\sum_{i=1}^{n}(Y_i - \bar{Y})^2}}$$
        The engine filters pairs by absolute strength $|r| \ge 0.40$ and ranks findings by significance:
        <br>&bull; <strong>Strong Correlation ($|r| \ge 0.70$):</strong> Flagged as High Priority insight.
        <br>&bull; <strong>Moderate Correlation ($0.40 \le |r| < 0.70$):</strong> Flagged as Medium Priority insight.
    </div>

    <h2>8.3 Empirical Correlation Matrix: Student Performance Dataset</h2>
    <p>Below is the empirical correlation output automatically surfaced from the pre-loaded <em>Student Academic Performance</em> domain dataset (800 records):</p>

    <table class="tech-table">
        <thead>
            <tr><th>Metric A</th><th>Metric B</th><th>Pearson $r$</th><th>Significance</th><th>Automated Executive Synthesis</th></tr>
        </thead>
        <tbody>
            <tr>
                <td class="mono">Attendance_Pct</td>
                <td class="mono">Final_Marks</td>
                <td class="mono" style="font-weight:700; color:#15803d;">+0.78</td>
                <td><span class="badge badge-green">Strong Positive</span></td>
                <td>Final marks show a strong positive relationship with class attendance ($r = 0.78$). Higher attendance consistently drives higher academic scores.</td>
            </tr>
            <tr>
                <td class="mono">Weekly_Study_Hours</td>
                <td class="mono">Final_Marks</td>
                <td class="mono" style="font-weight:700; color:#15803d;">+0.64</td>
                <td><span class="badge badge-green">Moderate Positive</span></td>
                <td>Weekly study hours directly correlate with improved marks ($r = 0.64$). Students studying $>25$ hrs/wk average Grade A.</td>
            </tr>
            <tr>
                <td class="mono">Midterm_Marks</td>
                <td class="mono">Final_Marks</td>
                <td class="mono" style="font-weight:700; color:#15803d;">+0.89</td>
                <td><span class="badge badge-green">Strong Positive</span></td>
                <td>Midterm scores serve as a reliable leading predictor ($r = 0.89$) for final graduation grades.</td>
            </tr>
        </tbody>
    </table>
    """

def get_page_19():
    return """
    <h1>Chapter 8.2: Outliers, Pareto & Temporal Trends</h1>
    <h2>8.4 Statistical Anomaly & Outlier Detection</h2>
    <p>Unusual transactions, sensor spikes, and data entry errors degrade decision models. The engine detects extreme observations using a dual statistical envelope: <strong>Z-Score ($> 3\sigma$)</strong> and <strong>Interquartile Range (IQR)</strong> fences.</p>

    <div class="code-snippet">
-- Vectorized Z-Score Anomaly Identification Query in InsightsEngine
WITH stats AS (
    SELECT AVG("{measure}") AS mean_val, STDDEV_SAMP("{measure}") AS std_val FROM dataset
)
SELECT COUNT(*) AS outlier_count
FROM dataset, stats
WHERE ABS("{measure}" - stats.mean_val) > (3.0 * stats.std_val);
    </div>

    <p>When the proportion of extreme points exceeds 2.0% of the dataset, the system generates a high-priority alert detailing the count, mean, standard deviation, and bounding thresholds.</p>

    <h2>8.5 Pareto Concentration Analysis (The 80/20 Distribution)</h2>
    <p>In many business domains, a tiny subset of categories drives the majority of volume. The engine computes cumulative share profiles to identify concentration risk:</p>

    <div class="callout callout-warning">
        <strong>Pareto Alert Invariant:</strong> If the single top category within a dimension accounts for $\ge 35\%$ of a continuous measure's total aggregate, an alert is triggered:
        <br><em>"High Segment Concentration: Category 'Enterprise Suite' dominates, accounting for 48.2% of overall Revenue."</em>
    </div>

    <h2>8.6 Chronological Trend & Net Trajectory Analysis</h2>
    <p>When a temporal attribute is present, the engine aggregates the primary measure chronologically into monthly periods (<span class="mono">strftime('%Y-%m')</span>) and computes net change:</p>
    $$\text{Net Change \%} = \left(\frac{V_{\text{terminal}} - V_{\text{initial}}}{V_{\text{initial}}}\right) \times 100$$
    <p>Swings exceeding $\pm 20\%$ are flagged as macroeconomic trend shifts, feeding directly into the automated executive takeaways banner on the dashboard.</p>
    """

def get_page_20():
    return """
    <h1>Chapter 9: AutoML Studio & Task Detection</h1>
    <h2>9.1 The Self-Configuring Machine Learning Pipeline</h2>
    <p>Traditional machine learning platforms require users to manually specify problem formulations, select algorithms, tune hyper-parameters, and write custom encoding pipelines. DataMind AI's <span class="mono">MLEngine</span> completely automates this workflow:</p>

    <div class="diagram-box">
Parquet Dataset + Optional Target Column
   │
   ├─► Step 1: Automatic Task Classification (Regression vs. Classification vs. Clustering)
   │
   ├─► Step 2: Feature Matrix Sanitization & ID Pruning
   │           &bull; Automatically excludes ID columns, timestamps, and target column
   │
   ├─► Step 3: ColumnTransformer Scikit-Learn Pipeline Assembly
   │           &bull; Numeric Features: SimpleImputer(median) ──► StandardScaler()
   │           &bull; Categorical Features: SimpleImputer('missing') ──► OneHotEncoder(ignore)
   │
   ├─► Step 4: Multi-Model Competitive Leaderboard Training (80/20 Train/Test Split)
   │
   ├─► Step 5: Metric Evaluation & Winning Model Serialization (.joblib)
   │
   └─► Step 6: Diagnostic Visualization Generation & What-If Metadata Compilation
    </div>

    <h2>9.2 Dynamic Task Type Classification Algorithm</h2>
    <p>When <span class="mono">task_type="auto"</span>, the engine evaluates target column characteristics to determine the appropriate mathematical formulation:</p>

    <div class="code-snippet">
if task_type == "auto":
    if target_col in df.columns:
        unique_vals = df[target_col].nunique()
        if pd.api.types.is_numeric_dtype(df[target_col]) and unique_vals > 10:
            task_type = "regression"
        else:
            task_type = "classification"
    else:
        task_type = "clustering"
    </div>

    <p>If the user does not specify a target variable, the engine selects the primary continuous measure for regression or the primary categorical dimension for classification.</p>
    """

def get_page_21():
    return """
    <h1>Chapter 9.2: Multi-Model Competitive Leaderboard</h1>
    <h2>9.3 Competitive Algorithm Suite</h2>
    <p>Rather than relying on a single estimator, the AutoML studio trains an ensemble of competitive algorithms under identical cross-validation conditions, ranking them on a standardized leaderboard:</p>

    <div class="grid-2">
        <div class="kpi-card">
            <div class="kpi-title">Regression Competitors</div>
            <p style="font-size: 7.8pt; margin: 3px 0;">&bull; <strong>Random Forest Regressor:</strong> 100 estimators, tree depth adaptive.<br>&bull; <strong>Gradient Boosting Regressor:</strong> Sequential gradient descent boosting.<br>&bull; <strong>Ridge Regression:</strong> L2-regularized linear baseline.<br>&bull; <strong>Decision Tree Regressor:</strong> White-box interpretable baseline.</p>
        </div>
        <div class="kpi-card">
            <div class="kpi-title">Classification Competitors</div>
            <p style="font-size: 7.8pt; margin: 3px 0;">&bull; <strong>Random Forest Classifier:</strong> Balanced class weights.<br>&bull; <strong>Gradient Boosting Classifier:</strong> Robust deviance optimization.<br>&bull; <strong>Logistic Regression:</strong> L2-regularized multinomial solver.<br>&bull; <strong>Decision Tree Classifier:</strong> Gini-impurity splitting.</p>
        </div>
    </div>

    <h2>9.4 Mathematical Evaluation Metrics Suite</h2>
    <p>The leaderboard evaluates candidates across a comprehensive matrix of performance metrics:</p>

    <table class="tech-table">
        <thead>
            <tr><th>Task Type</th><th>Primary Metric</th><th>Formula / Formulation</th><th>Interpretation Range</th></tr>
        </thead>
        <tbody>
            <tr>
                <td><strong>Regression</strong></td>
                <td><strong>Coefficient of Determination ($R^2$)</strong></td>
                <td>$$R^2 = 1 - \frac{\sum (y_i - \hat{y}_i)^2}{\sum (y_i - \bar{y})^2}$$</td>
                <td>$R^2 \in (-\infty, 1.0]$. Values $>0.80$ denote strong predictive fidelity.</td>
            </tr>
            <tr>
                <td><strong>Regression</strong></td>
                <td><strong>Mean Absolute Error (MAE)</strong></td>
                <td>$$\text{MAE} = \frac{1}{n}\sum_{i=1}^{n}|y_i - \hat{y}_i|$$</td>
                <td>Expressed in original target units ($). Robust to outlier penalties.</td>
            </tr>
            <tr>
                <td><strong>Regression</strong></td>
                <td><strong>Root Mean Squared Error (RMSE)</strong></td>
                <td>$$\text{RMSE} = \sqrt{\frac{1}{n}\sum_{i=1}^{n}(y_i - \hat{y}_i)^2}$$</td>
                <td>Penalizes large errors heavily; primary metric for model selection.</td>
            </tr>
            <tr>
                <td><strong>Classification</strong></td>
                <td><strong>Accuracy & F1-Score</strong></td>
                <td>$$\text{Accuracy} = \frac{TP + TN}{TP + TN + FP + FN}, \quad F_1 = \frac{2 \cdot P \cdot R}{P + R}$$</td>
                <td>Range $[0, 1]$. Harmonic mean balances precision and recall on skewed data.</td>
            </tr>
        </tbody>
    </table>
    """

print("Part 3 defined successfully.")
