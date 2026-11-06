(() => {
  "use strict";
  const API_BASE_URL = String(window.CALCULATOR_API_BASE_URL || "").replace(/\/$/, "");
  const HISTORY_KEY = "python-calculator-pro.history.v1";
  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => [...root.querySelectorAll(selector)];
  const sidebar = $("#sidebar"), scrim = $("[data-close-drawer]"), openButton = $("[data-open-drawer]");
  const navItems = $$("[data-tool]"), pageTitle = $("#page-title"), workspaceTitle = $("#workspace-title");
  const workspaceSubtitle = $("#workspace-subtitle"), workspace = $("#tool-workspace");
  const angleToggle = $("#angle-toggle"), angleButtons = $$("[data-angle]"), apiStatus = $("#api-status");
  let angleMode = "DEG", activeTool = "Scientific Calculator", capabilities = null, history = loadHistory(), isBusy = false;

  const descriptions = {
    "Scientific Calculator": "A precise space for everyday maths and advanced expressions.",
    "Equations": "Solve polynomial equations and inspect their mathematical roots.",
    "Advanced Maths Studio": "Explore graphing, spreadsheets, symbolic mathematics, geometry, 3D surfaces, statistics, and probability in the calculator workspace.",
    "Graphing Calculator": "Plot functions and implicit equations on the coordinate plane.",
    "Calculus": "Calculate derivatives, integrals, definite integrals, and limits.",
    "Matrix Calculator": "Run matrix arithmetic and linear algebra operations.",
    "Statistics": "Summarize a dataset with descriptive statistical measures.",
    "Probability & Combinatorics": "Calculate event probabilities, permutations, combinations, and binomial probabilities.",
    "Unit Converter": "Convert physical units, currencies, and number bases in one workspace.",
    "Finance & Loan EMI": "Calculate interest, compound growth, and fixed monthly loan instalments.",
    "Discount & GST Calculator": "Calculate discounts, GST, and tax-inclusive prices.",
    "Number Base Converter": "Convert integer values between number bases 2 and 36.",
    "BMI Calculator": "Calculate body mass index from height and weight.",
    "Date Calculator": "Add or subtract days and calculate the difference between dates."
  };
  const selectOptions = {
    calculusOperation: [["derivative","Derivative"],["integral","Indefinite integral"],["definite_integral","Definite integral"],["limit","Limit"]],
    statsOperation: [["mean","Mean"],["median","Median"],["mode","Mode"],["range","Range"],["minimum","Minimum"],["maximum","Maximum"],["variance","Sample variance"],["population_variance","Population variance"],["standard_deviation","Sample standard deviation"],["population_standard_deviation","Population standard deviation"],["quartiles","Quartiles"]],
    probabilityOperation: [["simple","Simple probability"],["complement","Complement"],["conditional","Conditional probability"],["union","Union"],["permutation","Permutation nPr"],["combination","Combination nCr"],["binomial","Binomial probability"]],
    matrixOperation: [["add","Add A + B"],["subtract","Subtract A − B"],["multiply","Multiply A × B"],["scalar_multiply","Scalar multiply"],["transpose","Transpose"],["power","Matrix power"],["trace","Trace"],["identity","Identity matrix"],["zero","Zero matrix"],["equals","Compare matrices"],["determinant","Determinant"],["minor","Minor"],["cofactor","Cofactor"],["adjoint","Adjoint"],["inverse","Inverse"],["rank","Rank"],["rref","Reduced row echelon form"],["solve","Solve Ax = b"],["cramer","Cramer's rule"],["lu","LU decomposition"],["eigen","Eigenvalues/eigenvectors"],["characteristic_polynomial","Characteristic polynomial"],["linear_independence","Linear independence"]],
    dateOperation: [["add_days","Add days"],["subtract_days","Subtract days"],["difference","Difference between dates"]],
    financeOperation: [["simple-interest","Simple interest"],["compound-interest","Compound interest"],["emi","Loan EMI"]]
  };
  const tools = {
    "Scientific Calculator": {kind:"scientific"},
    "Equations": {kind:"equation"},
    "Graphing Calculator": {kind:"graph"},
    "Advanced Maths Studio": {kind:"studio"},
    "Calculus": {kind:"calculus"},
    "Matrix Calculator": {kind:"matrix"},
    "Statistics": {kind:"statistics"},
    "Probability & Combinatorics": {kind:"probability"},
    "Unit Converter": {kind:"units"},
    "Finance & Loan EMI": {kind:"finance"},
    "Discount & GST Calculator": {kind:"discount"},
    "BMI Calculator": {kind:"bmi"},
    "Date Calculator": {kind:"date"}
  };

  function setDrawer(open) {
    sidebar.classList.toggle("is-open", open); scrim.hidden = !open;
    openButton.setAttribute("aria-expanded", String(open)); document.body.classList.toggle("drawer-open", open);
  }
  openButton.addEventListener("click", () => setDrawer(true));
  scrim.addEventListener("click", () => setDrawer(false));
  document.addEventListener("keydown", event => { if (event.key === "Escape") setDrawer(false); });

  function setApiStatus(connected, message) {
    apiStatus.replaceChildren();
    const dot = document.createElement("span"); dot.className = connected ? "status-dot" : "status-dot status-dot-muted";
    const label = document.createElement("span"); label.textContent = message; apiStatus.append(dot,label);
  }
  const API_TIMEOUT_MS = 90000; // Allow Render free instances time to wake after idle periods.
  async function api(path, body, {timeoutMs=API_TIMEOUT_MS} = {}) {
    if (!API_BASE_URL) throw new Error("The calculator API URL is missing. Reload the site after the latest Render deployment; if the problem continues, check the frontend API_BASE_URL setting.");
    const controller = new AbortController();
    const timeout = setTimeout(() => controller.abort(), timeoutMs);
    const options = body === undefined ? {method:"GET",signal:controller.signal} : {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body),signal:controller.signal};
    let response;
    try { response = await fetch(API_BASE_URL + path, options); }
    catch (error) {
      if (error && error.name === "AbortError") throw new Error("The calculator API took too long to respond. Please retry; if this continues, check the backend logs.");
      throw new Error("Could not reach the calculator API. Check that the backend is running and the API URL/CORS settings are correct.");
    } finally { clearTimeout(timeout); }
    let payload;
    try { payload = await response.json(); } catch { throw new Error("The API returned an unreadable response."); }
    if (!response.ok) {
      const details = payload?.error?.details;
      const firstDetail = Array.isArray(details) && details.length ? details.map(item => item.message).filter(Boolean).join(" ") : "";
      throw new Error(payload?.error?.message && payload.error.message !== "Request validation failed." ? payload.error.message : firstDetail || "The request could not be completed.");
    }
    return payload;
  }
  async function checkApi() {
    try {
      await api("/healthz"); setApiStatus(true,"API connected");
      try { capabilities = await api("/api/v1/capabilities"); if(activeTool==="Unit Converter")renderTool(activeTool); } catch { capabilities = null; }
    } catch { setApiStatus(false,"API offline"); }
  }

  function field(name, label, opts = {}) {
    const wrap = document.createElement("label"); wrap.className = "field";
    const caption = document.createElement("span"); caption.className = "field-label"; caption.textContent = label; wrap.append(caption);
    let control;
    if (opts.type === "select") {
      control = document.createElement("select");
      (opts.options || []).forEach(([value,text]) => { const option = document.createElement("option"); option.value=value; option.textContent=text; control.append(option); });
    } else if (opts.type === "textarea") {
      control = document.createElement("textarea"); control.rows = opts.rows || 3; control.placeholder = opts.placeholder || "";
    } else {
      control = document.createElement("input"); control.type = opts.type || "text"; control.placeholder = opts.placeholder || "";
      if (opts.min !== undefined) control.min = opts.min;
      if (opts.max !== undefined) control.max = opts.max;
      if (opts.step !== undefined) control.step = opts.step;
      if (opts.type === "number") control.step = opts.step || "any";
    }
    control.name=name; control.id="field-"+name; control.required = opts.required === true;
    if (opts.value !== undefined) control.value=opts.value;
    if (opts.help) { control.setAttribute("aria-describedby","help-"+name); const help=document.createElement("small");help.className="field-help";help.id="help-"+name;help.textContent=opts.help;wrap.append(control,help); }
    else wrap.append(control);
    return wrap;
  }
  const num = (name,label,value="0",help) => field(name,label,{type:"number",value,help});
  const txt = (name,label,value="",placeholder="",help) => field(name,label,{type:"text",value,placeholder,help});
  const sel = (name,label,opts) => field(name,label,{type:"select",options:opts});
  const area = (name,label,value,placeholder,help) => field(name,label,{type:"textarea",value,placeholder,help});
  function options(values) { return values.map(value => [value,value]); }
  function group(title, fields) {
    const section=document.createElement("section"); section.className="form-section";
    const heading=document.createElement("h3"); heading.textContent=title; section.append(heading);
    const grid=document.createElement("div"); grid.className="field-grid"; fields.forEach(f=>grid.append(f)); section.append(grid); return section;
  }
  function button(text, className="primary-button", type="submit") {
    const el=document.createElement("button"); el.type=type;el.className=className;el.textContent=text;return el;
  }
  function createPanel(title, description) {
    workspace.replaceChildren();
    const grid=document.createElement("div"); grid.className="workspace-grid tool-grid"; if(title==="Equations")grid.classList.add("equations-tool-grid");
    const panel=document.createElement("section");panel.className="panel tool-card";
    const head=document.createElement("div");head.className="tool-card-heading";
    const h=document.createElement("h2");h.textContent=title;head.append(h);
    const p=document.createElement("p");p.textContent=description;head.append(p);panel.append(head);
    const form=document.createElement("form");form.className="tool-form";
    const output=document.createElement("section");output.className="panel result-card";output.setAttribute("aria-live","polite");
    const outHead=document.createElement("div");outHead.className="panel-heading";
    const outTitle=document.createElement("h2");outTitle.textContent="Result";outHead.append(outTitle);output.append(outHead);
    const body=document.createElement("div");body.className="result-body";body.textContent="Enter values and run the calculation.";output.append(body);
    form.addEventListener("submit", async event => {
      event.preventDefault(); if(activeTool === "Scientific Calculator" || isBusy)return;
      const submit=form.querySelector('[type="submit"]');const original=submit.textContent;
      submit.disabled=true;submit.textContent="Calculating…";isBusy=true;form.querySelectorAll(".form-error").forEach(el=>el.remove());
      try {
        const result=await submitForm(form);
        renderResult(body,result,form);
        const inputs=[...form.querySelectorAll("input,select,textarea")].filter(el=>el.name&&el.value&&!el.closest(".field")?.hidden);
        const expression=activeTool+" · "+inputs.map(el=>el.name+"="+el.value).join(", ");
        const displayedResult=typeof result==="object"?(result.result!==undefined?String(result.result):result.message||result.status||JSON.stringify(result)):String(result);
        saveHistory({expression,displayedResult,timestamp:new Date().toISOString(),tool:activeTool});
        if(activeTool==="Equations"&&!result.graph_only) await appendEquationGraph(body,form,result);
      }
      catch(error) { body.replaceChildren();const message=document.createElement("p");message.className="result-error";message.textContent=error.message;body.append(message); }
      finally { submit.disabled=false;submit.textContent=original;isBusy=false; }
    });
    const actions=document.createElement("div");actions.className="form-actions";actions.append(button("Calculate"));
    form.append(actions);panel.append(form);grid.append(panel,output);workspace.append(grid);
    return {form,body,output};
  }
  function addFields(form, sections) { sections.forEach(([title,fields])=>form.insertBefore(group(title,fields),form.querySelector(".form-actions"))); }
  function addMathKeypad(form,title){
    const preferred=title==="Equations"?["equation","system_equations","expression"]:title==="Calculus"?["expression","lower","upper","point"]:["expression"];
    const named=preferred.map(name=>form.elements.namedItem(name)).filter(Boolean);
    const fallback=[...form.querySelectorAll("input:not([type=hidden]):not([type=submit]),textarea")].filter(el=>!el.disabled);
    const targets=[...new Set([...named,...fallback])];
    if(!targets.length)return;
    targets.forEach(control=>{control.setAttribute("inputmode","none");control.setAttribute("autocomplete","off");control.setAttribute("autocapitalize","off");});
    if(!targets.length)return;
    targets.forEach(control=>{control.setAttribute("inputmode","none");control.setAttribute("autocomplete","off");control.setAttribute("autocapitalize","off");});
    const keypad=document.createElement("div");keypad.className="math-keypad";keypad.setAttribute("aria-label","Math input keypad");
    const pages=[
      [["x","x"],["y","y"],["z","z"],["π","pi"],["e","e"],["√(","sqrt("],["sin(","sin("],["cos(","cos("],["tan(","tan("],["log(","log("],["ln(","ln("],["7","7"],["8","8"],["9","9"],["÷","/"],["4","4"],["5","5"],["6","6"],["×","*"],["1","1"],["2","2"],["3","3"],["−","-"],["0","0"],[".","."],["(","("],[")",")"],["^","^"],["+","+"],["=","="],["⌫","BACKSPACE"],["Clear","CLEAR"]],
      [["sin⁻¹","asin("],["cos⁻¹","acos("],["tan⁻¹","atan("],["sec","sec("],["csc","csc("],["cot","cot("],["cosec","cosec("],["sinh","sinh("],["cosh","cosh("],["tanh","tanh("],["abs","abs("],["exp","exp("],["√","sqrt("],["∛","cbrt("],["n!","factorial("],["%","%"],["mod","%"],["∞","oo"],[",",","],["⌫","BACKSPACE"],["Clear","CLEAR"]]
    ];
    const switcher=document.createElement("div");switcher.className="keypad-page-switcher";
    const keysWrap=document.createElement("div");keysWrap.className="math-keypad-keys";
    let page=0;
    const draw=()=>{keysWrap.replaceChildren();pages[page].forEach(([label,value])=>{
      const key=document.createElement("button");key.type="button";key.className="math-key";key.textContent=label;key.dataset.mathKey=value;
      key.addEventListener("mousedown",event=>event.preventDefault());
      key.addEventListener("click",()=>{
        const target=targets.find(control=>control===document.activeElement)||targets[0];
        const supportsSelection=target.tagName==="TEXTAREA"||["text","search","url","tel","password"].includes(target.type);
        if(!supportsSelection){
          if(value==="CLEAR")target.value="";
          else if(value==="BACKSPACE")target.value=target.value.slice(0,-1);
          else if(!["=","%","BACKSPACE"].includes(value))target.value+=value;
        }else{
          const start=Number.isInteger(target.selectionStart)?target.selectionStart:target.value.length;
          const end=Number.isInteger(target.selectionEnd)?target.selectionEnd:start;
          if(value==="CLEAR"){target.value="";target.setSelectionRange(0,0);}
          else if(value==="BACKSPACE"){const from=start===end?Math.max(0,start-1):start;target.value=target.value.slice(0,from)+target.value.slice(end);target.setSelectionRange(from,from);}
          else{const insert=value==="π"?"pi":value;target.setRangeText(insert,start,end,"end");}
        }
        target.dispatchEvent(new Event("input",{bubbles:true}));target.dispatchEvent(new Event("change",{bubbles:true}));target.focus();
      });keysWrap.append(key);
    });};
    [["123","Numbers & functions"],["ƒx","More functions"]].forEach(([label,aria],index)=>{const btn=document.createElement("button");btn.type="button";btn.className="keypad-page-button";btn.textContent=label;btn.setAttribute("aria-label",aria);btn.setAttribute("aria-pressed",String(index===0));btn.addEventListener("click",()=>{page=index;switcher.querySelectorAll("button").forEach((b,i)=>b.setAttribute("aria-pressed",String(i===page)));draw();});switcher.append(btn);});
    keypad.append(switcher,keysWrap);
    draw();
    form.insertBefore(keypad,form.querySelector(".form-actions"));
  }
  function val(form,name) { const el=form.elements.namedItem(name); return el ? el.value.trim() : ""; }
  function number(form,name) { const raw=val(form,name); const value=Number(raw); if(raw===""||!Number.isFinite(value))throw new Error("Enter a valid finite number for "+name.replaceAll("_"," ")+"."); return value; }
  function integer(form,name) { const value=number(form,name); if(!Number.isInteger(value))throw new Error(name.replaceAll("_"," ")+" must be a whole number.");return value; }
  function csvNumbers(form,name) { const values=val(form,name).split(/[\s,;]+/).filter(Boolean).map(Number);if(!values.length||values.some(v=>!Number.isFinite(v)))throw new Error("Enter one or more valid numbers separated by commas or spaces.");return values; }
  function matrixValue(form,name) {
    const raw=val(form,name);if(!raw)throw new Error("Enter matrix "+name.replace("matrix","").trim()+".");
    const rows=raw.split(/\n|;/).map(row=>row.trim()).filter(Boolean).map(row=>{
      // Commas let symbolic cells contain spaces, e.g. "x + 1, y"; numeric
      // matrices may still use the compact whitespace-separated format.
      const cells=row.includes(",")?row.split(","):row.split(/\s+/);
      return cells.map(token=>token.trim()).filter(Boolean).map(token=>{
        if(!/^[A-Za-z_π0-9.+*/^()\-]+$/.test(token))throw new Error("Use numeric values or safe matrix expressions such as x+1, sqrt(2), or 3/4. Separate symbolic cells with commas.");
        return token;
      });
    });
    if(!rows.length||rows.some(row=>row.length!==rows[0].length))throw new Error("Each matrix must be rectangular with the same number of values per row.");
    if(rows.length>8||rows[0].length>8)throw new Error("Matrix dimensions are limited to 8 × 8 by the API.");
    return rows;
  }
  function workedSolutionSteps(form,result) {
    if(!form || !result || typeof result!=="object") return [];
    const read=name=>{const el=form.elements.namedItem(name);return el?String(el.value).trim():"";};
    const n=name=>Number(read(name));
    const clean=value=>Number.isFinite(Number(value))?Number(value).toPrecision(8).replace(/(\.\d*?)0+$/,"$1").replace(/\.$/,""):String(value);
    const steps=[];
    const add=(title,detail)=>steps.push({title,detail:String(detail)});
    const operation=read("operation");
    if(activeTool==="Scientific Calculator"){
      const expression=read("expression");
      add("1. Read the expression",expression);
      add("2. Follow the order of operations","Evaluate brackets first, then powers and roots, then multiplication/division, and finally addition/subtraction. Functions such as sin, cos, and log are evaluated at their position in the expression.");
      add("3. Check angle mode","Trigonometric inputs use the selected "+angleMode+" mode. In DEG mode, angles are interpreted in degrees; in RAD mode, they are interpreted in radians.");
      if(result.exact_fraction)add("4. Exact form",String(result.exact_fraction));
      add("Final result",String(result.result??result.value??"See answer above."));
    } else if(activeTool==="Equations"){
      const mode=read("equation_mode");
      if(mode==="quadratic"||mode==="linear"||mode==="polynomial"){
        const equation=read("equation").replace(/[−–]/g,"-").replace(/\s+/g,"");
        const parts=equation.split("=");
        if(parts.length===2){
          const coeff={0:0,1:0,2:0};
          let valid=true;
          const parseSide=(side,multiplier)=>{
            const terms=side.match(/[+-]?[^+-]+/g)||[];
            for(const raw of terms){
              const term=raw.replace(/\*/g,"");
              const match=term.match(/^([+-]?)(?:(\d+(?:\.\d*)?|\.\d+))?(?:x(?:\^(\d+))?)?$/i);
              if(!match){valid=false;return;}
              const sign=match[1]==="-"?-1:1,hasX=/x/i.test(term),power=hasX?Number(match[3]||1):0;
              if(power>2){valid=false;return;}
              coeff[power]+=multiplier*sign*(match[2]===undefined?(hasX?1:0):Number(match[2]));
            }
          };
          parseSide(parts[0],1);parseSide(parts[1],-1);
          if(valid){
            const {0:c,1:b,2:a}=coeff;
            add("1. Rearrange the equation",equation+" = 0");
            if(mode==="quadratic"||a!==0){
              add("2. Identify the coefficients","Compare ax² + bx + c = 0. Here a = "+clean(a)+", b = "+clean(b)+", c = "+clean(c)+".");
              add("3. Write the quadratic formula","x = (−b ± √(b² − 4ac)) / 2a");
              const d=b*b-4*a*c;
              add("4. Calculate the discriminant","D = b² − 4ac = ("+clean(b)+")² − 4("+clean(a)+")("+clean(c)+") = "+clean(d)+".");
              add("5. Substitute into the formula","x = (−("+clean(b)+") ± √("+clean(d)+")) / (2 × "+clean(a)+").");
              if(Array.isArray(result.solutions)&&result.solutions.length){
                const roots=result.solutions.map((s,i)=>"x"+(i+1)+" = "+clean(s.real)+(Math.abs(Number(s.imaginary||0))>1e-10?" "+(s.imaginary<0?"−":"+")+" "+clean(Math.abs(s.imaginary))+"i":"")).join("; ");
                add("6. Final roots",roots);
              } else add("6. Interpret the discriminant",d<0?"D is negative, so there are no real roots.":d===0?"D is zero, so the equation has one repeated real root.":"D is positive, so the equation has two real roots.");
            }else{
              add("2. Isolate x",clean(b)+"x + ("+clean(c)+") = 0");
              add("3. Divide by the coefficient of x","x = −c / b = −("+clean(c)+") / "+clean(b)+".");
              if(result.solutions?.length)add("4. Final answer","x = "+clean(result.solutions[0].real));
            }
          }
        }
      } else if(mode==="binomial"){
        add("1. Identify the binomial","Start with "+read("expression")+".");
        add("2. Apply the binomial theorem","(a + b)ⁿ = Σ C(n,r) aⁿ⁻ʳ bʳ, for r = 0 to n.");
        add("3. Collect the terms","The symbolic engine expands each term and combines like terms.");
        add("4. Expanded result",result.expansion||"See the result above.");
      } else if(mode==="system"){
        add("1. List the equations",read("system_equations").split(/\n+/).filter(Boolean).join(" ; "));
        add("2. Solve simultaneously","The solver finds values that satisfy every equation at the same time.");
        add("3. Check the solution","Substitute each returned variable value into every original equation.");
      }
    } else if(activeTool==="Unit Converter"){
      const type=read("conversion_type");
      if(type==="units"){
        const value=n("value"),from=read("from_unit"),to=read("to_unit"),converted=Number(result.value);
        add("1. Start with the given quantity",clean(value)+" "+from);
        if(/celsius|fahrenheit|kelvin/i.test(from)||/celsius|fahrenheit|kelvin/i.test(to)){
          const formulas={"celsius→fahrenheit":"°F = (°C × 9/5) + 32","fahrenheit→celsius":"°C = (°F − 32) × 5/9","celsius→kelvin":"K = °C + 273.15","kelvin→celsius":"°C = K − 273.15","fahrenheit→kelvin":"K = (°F − 32) × 5/9 + 273.15","kelvin→fahrenheit":"°F = (K − 273.15) × 9/5 + 32"};
          add("2. Choose the conversion formula",formulas[(from+"→"+to).toLowerCase()]||"Temperature conversions use an offset as well as a scale factor.");
        } else {
          const factor=value!==0?converted/value:null;
          add("2. Use the unit conversion factor",factor===null?"The input is zero, so the converted value is also zero.": "1 "+from+" = "+clean(factor)+" "+to);
          add("3. Multiply by the conversion factor",clean(value)+" × "+(factor===null?"conversion factor":clean(factor))+" = "+clean(converted)+" "+to);
        }
        add("4. Final converted value",clean(converted)+" "+to);
      } else if(type==="base"){
        add("1. Interpret the source number",read("base_value")+" is written in base "+read("from_base")+".");
        add("2. Convert to base 10","Expand each digit using its positional power: Σ digit × "+read("from_base")+"^position.");
        add("3. Convert to the target base","Repeatedly divide the decimal integer by "+read("to_base")+" and read the remainders from last to first.");
        add("4. Final representation",String(result.result??result.value??"See result")+" in base "+read("to_base")+".");
      } else {
        add("1. Read the exchange amount",read("amount")+" "+read("from_currency").toUpperCase()+".");
        add("2. Apply the exchange rate","Multiply the amount by the provider's current "+read("from_currency").toUpperCase()+" → "+read("to_currency").toUpperCase()+" rate.");
        add("3. Converted amount",String(result.converted_amount??result.result??JSON.stringify(result)));
        add("Note","Currency rates can change; the displayed conversion uses the rate returned for this request.");
      }
    } else if(activeTool==="Finance & Loan EMI"){
      const p=n("principal"),rate=n("annual_rate")/100;
      if(operation==="simple-interest"){
        const t=n("years"),interest=Number(result.interest),total=Number(result.total_amount);
        add("1. Write the simple-interest formula","SI = (P × R × T) / 100");
        add("2. Substitute the values","SI = ("+clean(p)+" × "+clean(n("annual_rate"))+" × "+clean(t)+") / 100");
        add("3. Calculate the interest","SI = "+clean(interest));
        add("4. Add the principal","A = P + SI = "+clean(p)+" + "+clean(interest)+" = "+clean(total));
      } else if(operation==="compound-interest"){
        const t=n("years"),freq=n("compounding_per_year"),total=Number(result.total_amount);
        add("1. Write the compound-amount formula","A = P(1 + R/(100m))^(mt)");
        add("2. Identify the values","P = "+clean(p)+", R = "+clean(n("annual_rate"))+"%, m = "+freq+" times/year, t = "+clean(t)+" years.");
        add("3. Substitute","A = "+clean(p)+"(1 + "+clean(n("annual_rate"))+"/("+100*freq+"))^("+freq+" × "+clean(t)+")");
        add("4. Calculate compound amount","A = "+clean(total));
        add("5. Find compound interest","CI = A − P = "+clean(total)+" − "+clean(p)+" = "+clean(result.interest));
      } else {
        const months=n("tenure_months"),r=rate/12,emi=Number(result.monthly_emi);
        add("1. Convert annual interest to a monthly rate","r = annual rate / 12 / 100 = "+clean(r));
        add("2. Set the number of instalments","n = "+months+" months.");
        add("3. Write the EMI formula","EMI = P × r × (1+r)ⁿ / ((1+r)ⁿ − 1)");
        add("4. Substitute the values","EMI = "+clean(p)+" × "+clean(r)+" × (1+"+clean(r)+")^"+months+" / ((1+"+clean(r)+")^"+months+" − 1)");
        add("5. Monthly instalment","EMI = "+clean(emi));
        add("6. Total repayment and interest","Total = EMI × n = "+clean(result.total_payment)+"; interest = total − principal = "+clean(result.total_interest));
      }
    } else if(activeTool==="Discount & GST Calculator"){
      const amount=n("price"),rate=n(read("operation")==="discount"?"discount_percent":"gst_rate");
      if(read("operation")==="discount"){
        add("1. Discount formula","Discount = Original price × Discount rate / 100");
        add("2. Substitute","Discount = "+clean(amount)+" × "+clean(rate)+" / 100");
        add("3. Calculate discount","Discount = "+clean(result.discount_amount));
        add("4. Subtract from original price","Final price = "+clean(amount)+" − "+clean(result.discount_amount)+" = "+clean(result.final_price));
      }else if(read("inclusive")==="true"){
        add("1. Extract the pre-tax amount","Base = Inclusive amount / (1 + GST rate/100)");
        add("2. Substitute","Base = "+clean(amount)+" / (1 + "+clean(rate)+"/100) = "+clean(result.base_amount));
        add("3. Find the GST component","GST = Inclusive amount − Base = "+clean(result.gst_amount));
      }else{
        add("1. Calculate GST","GST = Amount × GST rate / 100");
        add("2. Substitute","GST = "+clean(amount)+" × "+clean(rate)+" / 100 = "+clean(result.gst_amount));
        add("3. Add tax to the base amount","Total = "+clean(amount)+" + "+clean(result.gst_amount)+" = "+clean(result.total_amount));
      }
    } else if(activeTool==="BMI Calculator"){
      const weight=n("weight_kg"),height=read("height_unit")==="imperial"?(n("height_feet")*12+n("height_inches"))*0.0254:n("height_cm")/100;
      add("1. Convert height to metres",read("height_unit")==="imperial"?"Height = (feet × 12 + inches) × 0.0254 = "+clean(height)+" m":"Height = centimetres / 100 = "+clean(height)+" m");
      add("2. Write the BMI formula","BMI = weight (kg) / [height (m)]²");
      add("3. Substitute the measurements","BMI = "+clean(weight)+" / ("+clean(height)+")²");
      add("4. Calculate BMI","BMI = "+clean(result.bmi));
      add("Interpretation","BMI is a screening measure, not a diagnosis. For people under 18, adult BMI category labels are not appropriate; age- and sex-specific growth charts are needed.");
    } else if(activeTool==="Date Calculator"){
      if(operation==="difference"){
        add("1. Identify the two dates",read("date")+" and "+read("other_date")+".");
        add("2. Calculate the elapsed calendar days","Subtract the earlier date from the later date using calendar-day arithmetic.");
        add("3. Day difference",String(result.days_difference)+" days (signed); absolute difference = "+result.absolute_days+" days.");
      }else{
        add("1. Start with the date",read("date")+".");
        add("2. Apply the day offset",operation==="add_days"?"Move forward by "+read("days")+" calendar days.":"Move backward by "+read("days")+" calendar days.");
        add("3. Resulting date",String(result.result_date)+". Calendar months and leap years are handled automatically.");
      }
    } else if(activeTool==="Statistics"){
      const values=read("values").split(/[\s,;]+/).filter(Boolean).map(Number),sorted=[...values].sort((a,b)=>a-b),mean=values.reduce((a,b)=>a+b,0)/values.length;
      const label={mean:"Arithmetic mean",median:"Median",mode:"Mode",range:"Range",minimum:"Minimum",maximum:"Maximum",variance:"Sample variance",population_variance:"Population variance",standard_deviation:"Sample standard deviation",population_standard_deviation:"Population standard deviation",quartiles:"Quartiles"}[operation]||operation;
      add("1. Prepare the data",values.join(", "));
      if(operation==="mean"){add("2. Use the mean formula","Mean = sum of observations / number of observations");add("3. Substitute","Mean = ("+values.join(" + ")+") / "+values.length+" = "+clean(result.result));}
      else if(operation==="median"){add("2. Sort the values",sorted.join(", "));add("3. Locate the middle value",values.length%2?"There are an odd number of values, so take the middle observation.":"There are an even number of values, so average the two middle observations.");add("4. Median",clean(result.result));}
      else if(operation==="range"){add("2. Find maximum and minimum","Range = maximum − minimum = "+clean(Math.max(...values))+" − "+clean(Math.min(...values))+" = "+clean(result.result));}
      else if(["variance","population_variance","standard_deviation","population_standard_deviation"].includes(operation)){add("2. Calculate the mean","Mean = "+clean(mean));add("3. Find each squared deviation","Calculate (xᵢ − mean)² for every observation, then add them.");add("4. Divide by the correct count",operation.includes("population")?"Population variance divides by N.":"Sample variance divides by n − 1.");add("5. Final "+label.toLowerCase(),clean(result.result));}
      else {add("2. Apply the definition",operation==="mode"?"Find the value(s) occurring most often.":operation==="minimum"?"Choose the smallest observation.":operation==="maximum"?"Choose the largest observation.":"Split the ordered data into lower and upper halves and find their medians.");add("3. Result",JSON.stringify(result.result));}
    } else if(activeTool==="Probability & Combinatorics"){
      const v=key=>n(key);
      if(operation==="simple"){add("1. Use the probability formula","P(E) = favourable outcomes / total outcomes");add("2. Substitute","P(E) = "+v("favorable")+" / "+v("total"));add("3. Calculate","P(E) = "+clean(result.result));}
      else if(operation==="complement"){add("1. Use the complement rule","P(A′) = 1 − P(A)");add("2. Substitute","P(A′) = 1 − "+v("event_a")+" = "+clean(result.result));}
      else if(operation==="conditional"){add("1. Use conditional probability","P(A | B) = P(A ∩ B) / P(B)");add("2. Substitute","P(A | B) = "+v("intersection")+" / "+v("event_b")+" = "+clean(result.result));}
      else if(operation==="union"){add("1. Use the addition rule","P(A ∪ B) = P(A) + P(B) − P(A ∩ B)");add("2. Substitute","= "+v("event_a")+" + "+v("event_b")+" − "+v("intersection"));add("3. Calculate","P(A ∪ B) = "+clean(result.result));}
      else if(operation==="permutation"||operation==="combination"){add("1. Identify n and r","n = "+v("n")+", r = "+v("r")+".");add("2. Write the formula",operation==="permutation"?"nPr = n! / (n − r)!":"nCr = n! / [r!(n − r)!]");add("3. Substitute","= "+(operation==="permutation"?"("+v("n")+"!)/("+v("n")+" − "+v("r")+")!":v("n")+"! / ["+v("r")+"! × ("+v("n")+" − "+v("r")+")!]"));add("4. Calculate",String(result.result));}
      else {add("1. Use the binomial probability formula","P(X = k) = C(n,k) pᵏ (1−p)ⁿ⁻ᵏ");add("2. Identify values","n = "+v("n")+", k = "+v("k")+", p = "+v("p")+".");add("3. Substitute","P(X = "+v("k")+") = C("+v("n")+","+v("k")+") × "+v("p")+"^"+v("k")+" × (1−"+v("p")+")^("+v("n")+"−"+v("k")+")");add("4. Calculate",clean(result.result));}
    } else if(activeTool==="Calculus"){
      const expression=read("expression"),variable=read("variable")||"x";
      if(operation==="derivative"){add("1. Identify the function","f("+variable+") = "+expression);add("2. Apply differentiation rules","Use the power rule, constant multiple rule, sum rule, and chain/product rules as required.");add("3. Symbolic derivative","d"+(read("order")==="1"?"":"⁽"+read("order")+"⁾")+"f / d"+variable+(read("order")==="1"?"":"⁽"+read("order")+"⁾")+" = "+result.result);}
      else if(operation==="integral"){add("1. Identify the integrand","∫ ("+expression+") d"+variable);add("2. Apply integration rules","Find an antiderivative whose derivative equals the integrand.");add("3. Include the constant of integration","∫ f("+variable+") d"+variable+" = "+result.result+" + C (where supported).");}
      else if(operation==="definite_integral"){add("1. Set up the definite integral","∫ from "+read("lower")+" to "+read("upper")+" of ("+expression+") d"+variable);add("2. Find an antiderivative","Let F′("+variable+") = f("+variable+").");add("3. Apply the Fundamental Theorem of Calculus","F("+read("upper")+") − F("+read("lower")+") = "+result.result);}
      else {add("1. State the limit","lim as "+variable+" → "+read("point")+" of ("+expression+").");add("2. Evaluate symbolically","The symbolic engine evaluates the requested one-sided or two-sided limit.");add("3. Limit value",String(result.result));}
    } else if(activeTool==="Graphing Calculator"){
      add("1. Interpret the input","The expression defines y as a function of x, or an implicit relation in x and y.");
      add("2. Sample the requested interval","The graph engine evaluates the expression at evenly spaced x-coordinates and keeps undefined points as gaps.");
      add("3. Plot the coordinates","Each valid (x, y) pair is mapped onto the coordinate plane; the curve is an approximation based on the sample density.");
    } else if(activeTool==="Matrix Calculator"){
      add("1. Identify the matrix operation","The selected operation is "+operation.replaceAll("_"," ")+".");
      add("2. Apply the corresponding linear-algebra rule","The requested operation is applied to the entered matrix or matrices.");
      add("3. Review row operations and intermediate matrices","For detailed matrix working, enable the server-generated step-by-step option; the result includes the exact row-operation sequence when supported.");
    }
    return steps;
  }

  function appendWorkedSolution(container,form,result) {
    const steps=Array.isArray(result?.steps)&&result.steps.length
      ? result.steps.map((step,index)=>({title:step.title||"Step "+(index+1),detail:step.detail||String(step)}))
      : workedSolutionSteps(form,result);
    if(!steps.length)return;
    const section=document.createElement("section");section.className="worked-solution";
    const heading=document.createElement("h3");heading.textContent="Step-by-step solution";
    const intro=document.createElement("p");intro.className="worked-solution-intro";intro.textContent="A worked explanation showing the formula, substitution, and reasoning behind the result.";
    const list=document.createElement("ol");
    steps.forEach(step=>{const item=document.createElement("li");const title=document.createElement("strong");title.textContent=step.title;const detail=document.createElement("p");detail.textContent=step.detail;item.append(title,detail);list.append(item);});
    section.append(heading,intro,list);container.append(section);
  }

  function exactTrigValue(expression) {
    const source=String(expression||"").trim().replace(/\s+/g,"").toLowerCase();
    const match=source.match(/^(sin|cos|tan)\(?([+-]?\d+(?:\.\d+)?)\)?$/);
    if(!match)return null;
    const fn=match[1],angle=Number(match[2]);
    if(angleMode==="RAD")return null;
    const normalized=((angle%360)+360)%360;
    const values={
      sin:{0:"0",30:"1/2",45:"√2/2",60:"√3/2",90:"1",120:"√3/2",135:"√2/2",150:"1/2",180:"0",210:"−1/2",225:"−√2/2",240:"−√3/2",270:"−1",300:"−√3/2",315:"−√2/2",330:"−1/2"},
      cos:{0:"1",30:"√3/2",45:"√2/2",60:"1/2",90:"0",120:"−1/2",135:"−√2/2",150:"−√3/2",180:"−1",210:"−√3/2",225:"−√2/2",240:"−1/2",270:"0",300:"1/2",315:"√2/2",330:"√3/2"},
      tan:{0:"0",30:"√3/3",45:"1",60:"√3",120:"−√3",135:"−1",150:"−√3/3",180:"0",210:"√3/3",225:"1",240:"√3",300:"−√3",315:"−1",330:"−√3/3"}
    };
    return values[fn][String(normalized)]||null;
  }
  function renderResult(container,result,sourceForm=null) {
    container.replaceChildren();
    if(activeTool==="Equations"&&sourceForm&&["linear","quadratic"].includes(val(sourceForm,"equation_mode"))&&result&&typeof result==="object"&&!Array.isArray(result)&&!Array.isArray(result.solutions)){
      const candidates=[result.value_1,result.value_2,result.value1,result.value2,result.root_1,result.root_2].filter(value=>value!==undefined&&value!==null&&value!=="");
      if(candidates.length)result={...result,solutions:candidates.map(value=>typeof value==="object"?value:{real:Number(value),imaginary:0}),status:result.status||"solved"};
    }
    const isRecord=value=>value!==null&&typeof value==="object"&&!Array.isArray(value);
    const heading=(text)=>{const el=document.createElement("h3");el.className="result-summary-title";el.textContent=text;container.append(el);return el;};
    const text=(value)=>value===null||value===undefined?"—":typeof value==="string"?value:typeof value==="number"?formatNumber(value):JSON.stringify(value);
    const row=(label,value)=>{
      const item=document.createElement("div");item.className="result-value-row";
      const term=document.createElement("span");term.className="result-value-label";term.textContent=label.replaceAll("_"," ");
      const detail=document.createElement("strong");detail.className="result-value-content";detail.textContent=text(value);
      item.append(term,detail);container.append(item);
    };
    if(isRecord(result)&&Array.isArray(result.relations)&&result.relations.length){
      heading("Equation relation");
      if(result.message){const message=document.createElement("p");message.className="result-summary-message";message.textContent=result.message;container.append(message);}
      if(Number.isInteger(result.degree))row("total_degree",result.degree);
      result.relations.forEach(relation=>{const expression=document.createElement("p");expression.className="result-expression";expression.textContent=relation;container.append(expression);});
      if(Array.isArray(result.variables)&&result.variables.length){const variables=document.createElement("p");variables.className="field-help";variables.textContent="Variables: "+result.variables.join(", ")+". This is one equation in multiple variables, not a system of equations.";container.append(variables);}
    } else if(isRecord(result)&&Array.isArray(result.segments)){
      heading(activeTool==="Equations"?"Parabola / relation graph":"Equation graph");
      const bounds=result.bounds||{};
      const graphForm=document.querySelector(".tool-form");
      const relation=typeof result.relation==="string"?result.relation:activeTool==="Graphing Calculator"&&graphForm?val(graphForm,"expression").replace(/[−–]/g,"-").trim():null;
      container.append(drawRelationGraph(result.segments,bounds,relation));
      row("curve_segments",result.segments.length);
    } else if(isRecord(result)&&Array.isArray(result.points)){
      const finite=result.points.filter(point=>point&&point.y!==null&&point.y!==undefined&&Number.isFinite(Number(point.x))&&Number.isFinite(Number(point.y)));
      const graphHeading=heading(activeTool==="Graphing Calculator"?"Function graph":"Graph");
      graphHeading.classList.add("graph-result-heading");
      if(finite.length>=2){
        const graphForm=document.querySelector(".tool-form");let graphExpression=null,graphXMin=null,graphXMax=null;if(activeTool==="Graphing Calculator"&&graphForm){graphExpression=val(graphForm,"expression").replace(/[−–]/g,"-").trim();if(/^\s*(?:x\s*=\s*y|y\s*=\s*x)\s*$/i.test(graphExpression))graphExpression="x";graphXMin=Number(val(graphForm,"x_min"));graphXMax=Number(val(graphForm,"x_max"));}container.append(drawGraph(result.points.map(point=>({x:Number(point.x),y:point.y===null?null:Number(point.y)})),{expression:graphExpression,xMin:graphXMin,xMax:graphXMax}));
      } else {
        const message=document.createElement("p");message.className="result-error";
        message.textContent=result.points.length?"The API returned samples, but fewer than two points have defined real values. Try a different range or function.":"The API returned no graph samples. Please try again.";
        container.append(message);
      }
      row("sample_points",result.points.length);
      row("defined_samples",finite.length);
    } else if(activeTool==="BMI Calculator" && isRecord(result) && Number.isFinite(Number(result.bmi))){
      heading("Your BMI");
      const value=document.createElement("p");value.className="result-primary-value bmi-primary-value";value.textContent=formatNumber(Number(result.bmi));container.append(value);
      const bmi=Number(result.bmi),bands=[{label:"Underweight",min:0,max:18.5,cls:"bmi-band-under"},{label:"Normal",min:18.5,max:25,cls:"bmi-band-normal"},{label:"Overweight",min:25,max:30,cls:"bmi-band-over"},{label:"Obese",min:30,max:40,cls:"bmi-band-obese"}];
      const scale=document.createElement("section");scale.className="bmi-scale-card";
      const scaleTitle=document.createElement("h4");scaleTitle.textContent="BMI range";scale.append(scaleTitle);
      const track=document.createElement("div");track.className="bmi-scale-track";track.setAttribute("role","img");track.setAttribute("aria-label","BMI scale: underweight below 18.5, normal 18.5 to 24.9, overweight 25 to 29.9, obese 30 and above.");
      bands.forEach(b=>{const segment=document.createElement("span");segment.className="bmi-scale-segment "+b.cls;segment.style.width=((b.max-b.min)/40*100)+"%";track.append(segment);});
      const marker=document.createElement("span");marker.className="bmi-scale-marker";marker.style.left=(Math.max(0,Math.min(40,bmi))/40*100)+"%";marker.title="BMI "+formatNumber(bmi);track.append(marker);scale.append(track);
      const labels=document.createElement("div");labels.className="bmi-scale-labels";bands.forEach(b=>{const item=document.createElement("span");item.textContent=b.label;labels.append(item);});scale.append(labels);
      const ticks=document.createElement("div");ticks.className="bmi-scale-ticks";["0","18.5","25","30","40+"].forEach(t=>{const item=document.createElement("span");item.textContent=t;ticks.append(item);});scale.append(ticks);
      const category=bmi<18.5?"Underweight":bmi<25?"Normal":bmi<30?"Overweight":"Obese";
      const summary=document.createElement("p");summary.className="bmi-category-line";summary.textContent="Reference band: "+category;scale.append(summary);
      const age=Number(sourceForm?.elements?.age?.value||18);
      const note=document.createElement("p");note.className="bmi-scale-note";note.textContent=age<18?"For ages 15–17, adult BMI bands are only a rough visual reference. A proper interpretation uses age- and sex-specific growth charts.":"BMI is a screening measure, not a diagnosis; it does not describe body composition or overall health.";scale.append(note);
      container.append(scale);
      row("weight_kg",result.weight_kg);row("height_m",result.height_m);
    } else if(activeTool==="Equations" && val(document.querySelector(".tool-form")||{elements:{}}, "equation_mode")==="polynomial" && isRecord(result) && typeof result.status==="string"){
      heading(result.status==="solved"?"Polynomial roots":result.status==="no_solution"?"No solution":"Polynomial relation");
      if(result.message){const message=document.createElement("p");message.className="result-summary-message";message.textContent=result.message;container.append(message);}
      if(Number.isInteger(result.degree))row("total_degree",result.degree);
      if(Array.isArray(result.relations))result.relations.forEach(relation=>{const expression=document.createElement("p");expression.className="result-expression";expression.textContent=relation;container.append(expression);});
      if(Array.isArray(result.solutions))result.solutions.forEach((solution,index)=>{const real=Number(solution.real),imag=Number(solution.imaginary||0);const line=document.createElement("div");line.className="root-result";const label=document.createElement("span");label.textContent="Root "+(index+1);const answer=document.createElement("strong");answer.textContent="x = "+formatNumber(real)+(Math.abs(imag)<1e-12?"":(imag<0?" − ":" + ")+formatNumber(Math.abs(imag))+"i");line.append(label,answer);container.append(line);});
    } else if(isRecord(result)&&Array.isArray(result.variables)&&Array.isArray(result.solutions)&&typeof result.status==="string"){
      heading(result.status==="solved"?"System solutions":result.status==="infinite_solutions"?"Underdetermined system":"No solution");
      if(result.message){const message=document.createElement("p");message.className="result-summary-message";message.textContent=result.message;container.append(message);}
      result.solutions.forEach((solution,index)=>{
        const section=document.createElement("section");section.className="system-solution";
        const title=document.createElement("h4");title.textContent="Solution "+(index+1);section.append(title);
        result.variables.forEach(variable=>{const item=document.createElement("div");item.className="result-value-row";const label=document.createElement("span");label.className="result-value-label";label.textContent=variable;const answer=document.createElement("strong");answer.className="result-value-content";answer.textContent=solution[variable]===undefined?"Free variable":String(solution[variable]);item.append(label,answer);section.append(item);});
        container.append(section);
      });
    } else if(activeTool==="Equations" && ["linear","quadratic"].includes(val(document.querySelector(".tool-form")||{elements:{}}, "equation_mode")) && isRecord(result) && Array.isArray(result.solutions) && typeof result.status==="string"){
      const mode=val(document.querySelector(".tool-form")||{elements:{}}, "equation_mode");
      heading(result.status==="solved"?"Answer":result.status==="no_solution"?"No solution":"Equation result");
      if(result.message){const message=document.createElement("p");message.className="result-summary-message";message.textContent=result.message;container.append(message);}
      if(result.status==="solved" && result.solutions.length){
        const note=document.createElement("p");note.className="result-summary-message";note.textContent=mode==="quadratic"?"The values below are the roots of the quadratic equation.":"The value below satisfies the equation.";container.append(note);
        const values=result.solutions.map(root=>{
          const real=Number(root.real),imag=Number(root.imaginary||0);
          if(Math.abs(imag)<1e-12)return formatNumber(real);
          return formatNumber(real)+(imag<0?" − ":" + ")+formatNumber(Math.abs(imag))+"i";
        });
        const line=document.createElement("div");line.className="root-result";
        const label=document.createElement("span");label.textContent="Answer";
        const answer=document.createElement("strong");answer.textContent="x = "+values.join(" or x = ");
        line.append(label,answer);container.append(line);
      } else if(!result.solutions.length && !result.message){
        const message=document.createElement("p");message.className="result-summary-message";message.textContent="No individual roots were returned for this equation.";container.append(message);
      }
    } else if(isRecord(result)&&Array.isArray(result.solutions)&&typeof result.status==="string"){
      const status=result.status==="solved"?"Solutions found":result.status==="no_solution"?"No solution":result.status==="infinite_solutions"?"Infinite solutions":"Solver result";
      heading(status);
      if(result.message){const message=document.createElement("p");message.className="result-summary-message";message.textContent=result.message;container.append(message);}
      if(result.solutions.length){
        result.solutions.forEach((root,index)=>{
          const real=Number(root.real),imag=Number(root.imaginary||0);
          let value;
          if(Math.abs(imag)<1e-12)value="x = "+formatNumber(real);
          else value="x = "+formatNumber(real)+(imag<0?" − ":" + ")+formatNumber(Math.abs(imag))+"i";
          const line=document.createElement("div");line.className="root-result";
          const label=document.createElement("span");label.textContent="Root "+(index+1);
          const answer=document.createElement("strong");answer.textContent=value;line.append(label,answer);container.append(line);
        });
      }
      if(!result.solutions.length&&!result.message){const msg=document.createElement("p");msg.className="result-summary-message";msg.textContent="The solver returned no individual roots.";container.append(msg);}
    } else if(isRecord(result)&&typeof result.expansion==="string"){
      heading("Expanded expression");
      const expression=document.createElement("p");expression.className="result-expression";expression.textContent=result.expansion;container.append(expression);
    } else if(isRecord(result)){
      if(typeof result.result==="number"||typeof result.result==="string"){
        heading("Answer");const answer=document.createElement("p");answer.className="result-primary-value";answer.textContent=text(result.result);container.append(answer);
      }
      if(activeTool==="Scientific Calculator"&&sourceForm&&!result.exact_fraction){
        const exact=exactTrigValue(val(sourceForm,"expression"));
        if(exact)row("exact_value",exact);
      }
      Object.entries(result).forEach(([key,value])=>{
        if(key==="result"&&(typeof value==="number"||typeof value==="string"))return;
        if(activeTool==="Scientific Calculator"&&key==="exact_fraction"&&!value)return;
        if(["value_1","value_2","value1","value2","root_1","root_2"].includes(key)&&Array.isArray(result.solutions))return;
        if(key==="points"||key==="solutions"||key==="expansion")return;
        if(Array.isArray(value)&&/step|working|derivation/i.test(key)){
          const section=document.createElement("section");section.className="solution-steps";
          const title=document.createElement("h3");title.textContent=key.replaceAll("_"," ");section.append(title);
          const list=document.createElement("ol");
          value.forEach(item=>{
            const li=document.createElement("li");
            if(item!==null&&typeof item==="object"&&!Array.isArray(item)){
              const parts=Object.entries(item).map(([name,detail])=>name.replaceAll("_"," ")+": "+text(detail));
              li.textContent=parts.join(" · ");
            } else li.textContent=text(item);
            list.append(li);
          });
          section.append(list);container.append(section);
        } else if(Array.isArray(value)||isRecord(value)){
          const details=document.createElement("details");details.className="result-nested";
          const summary=document.createElement("summary");summary.textContent=key.replaceAll("_"," ");details.append(summary);
          const pre=document.createElement("pre");pre.textContent=JSON.stringify(value,null,2);details.append(pre);container.append(details);
        } else row(key,value);
      });
    } else {
      const value=document.createElement("p");value.className="result-primary-value";value.textContent=text(result);container.append(value);
    }
    if(sourceForm) appendWorkedSolution(container,sourceForm,result);
    const details=document.createElement("details");details.className="result-raw-details";
    const summary=document.createElement("summary");summary.textContent="Technical response";details.append(summary);
    const pre=document.createElement("pre");pre.className="result-json";pre.textContent=typeof result==="string"?result:JSON.stringify(result,null,2);details.append(pre);container.append(details);
    const copy=button("Copy result","secondary-button","button");
    copy.addEventListener("click",async()=>{const content=pre.textContent;try{await navigator.clipboard.writeText(content);copy.textContent="Copied";}catch{const ta=document.createElement("textarea");ta.value=content;document.body.append(ta);ta.select();const ok=document.execCommand("copy");ta.remove();copy.textContent=ok?"Copied":"Copy unavailable";}});
    container.append(copy);
  }
  function drawGraph(points, options={}) {
    const figure=document.createElement("figure");figure.className="graph-figure";
    const width=900,height=520,pad={left:68,right:24,top:24,bottom:54};
    const plotW=width-pad.left-pad.right,plotH=height-pad.top-pad.bottom;
    const valid=points.filter(p=>Number.isFinite(p.x)&&Number.isFinite(p.y));
    if(valid.length<2){const msg=document.createElement("figcaption");msg.textContent="Not enough finite samples to draw this graph.";figure.append(msg);return figure;}
    const initialXMin=Number.isFinite(options.xMin)?options.xMin:Math.min(...valid.map(p=>p.x));
    const initialXMax=Number.isFinite(options.xMax)?options.xMax:Math.max(...valid.map(p=>p.x));
    if(initialXMin>=initialXMax){const msg=document.createElement("figcaption");msg.textContent="Invalid x-range returned by the API.";figure.append(msg);return figure;}
    const yValues=valid.map(p=>p.y),rawYMin=Math.min(...yValues),rawYMax=Math.max(...yValues);
    const rawYSpan=Math.max(rawYMax-rawYMin,Math.max(1,Math.abs(rawYMin)*.1));
    let xSpan=initialXMax-initialXMin;
    // Use equal units-per-pixel so straight lines and curves are not distorted.
    let ySpan=Math.max(rawYSpan*1.15,xSpan*plotH/plotW);
    xSpan=ySpan*plotW/plotH;
    const centerX=(initialXMin+initialXMax)/2,centerY=(rawYMin+rawYMax)/2;
    const view={xmin:centerX-xSpan/2,xmax:centerX+xSpan/2,ymin:centerY-ySpan/2,ymax:centerY+ySpan/2};
    const initialView={...view};
    const svgNS="http://www.w3.org/2000/svg";
    const svg=document.createElementNS(svgNS,"svg");svg.setAttribute("viewBox",`0 0 ${width} ${height}`);svg.setAttribute("role","img");svg.setAttribute("aria-label","Interactive coordinate graph with labelled axes. Drag to pan, pinch or scroll to zoom.");
    const controls=document.createElement("div");controls.className="graph-controls";controls.setAttribute("aria-label","Graph controls");
    const caption=document.createElement("figcaption");caption.textContent="Coordinates stay true to scale. Drag to pan; pinch, scroll, or use +/− to zoom. The graph resamples as you move.";
    let sampled=points,requestTimer=null,requestVersion=0,drag=null,lastPinch=0,selectedPoint=null;
    const pointers=new Map();
    const fmt=v=>{if(Math.abs(v)<1e-9)return "0";if(Math.abs(v)>=1e5||Math.abs(v)<1e-3)return v.toExponential(1);return Number(v.toPrecision(4)).toString();};
    const niceStep=range=>{const raw=range/8,power=Math.pow(10,Math.floor(Math.log10(Math.max(raw,1e-12)))),fraction=raw/power;return (fraction<1.5?1:fraction<3.5?2:fraction<7.5?5:10)*power;};
    const node=(tag,attrs={},textValue)=>{const el=document.createElementNS(svgNS,tag);Object.entries(attrs).forEach(([k,v])=>el.setAttribute(k,String(v)));if(textValue!==undefined)el.textContent=textValue;return el;};
    const scheduleResample=()=>{
      if(!options.expression)return;
      if(requestTimer!==null)clearTimeout(requestTimer);
      requestTimer=setTimeout(async()=>{
        const version=++requestVersion,lo=view.xmin,hi=view.xmax;
        try{const result=await api("/api/v1/graph/sample",{expression:options.expression,x_min:lo,x_max:hi,points:1001},{timeoutMs:10000});
          if(version!==requestVersion||!Array.isArray(result.points))return;
          sampled=result.points.map(p=>({x:Number(p.x),y:p.y===null?null:Number(p.y)}));caption.textContent="Coordinates stay true to scale. Drag to pan; pinch, scroll, or use +/− to zoom. The graph resamples as you move.";render();
        }catch(error){if(version===requestVersion)caption.textContent="Graph refresh failed: "+error.message+" The last valid curve is still shown.";}
      },110);
    };
    const render=()=>{
      svg.replaceChildren();
      const px=x=>pad.left+(x-view.xmin)/(view.xmax-view.xmin)*plotW;
      const py=y=>pad.top+(view.ymax-y)/(view.ymax-view.ymin)*plotH;
      const xStep=niceStep(view.xmax-view.xmin),yStep=niceStep(view.ymax-view.ymin);
      const xStart=Math.ceil(view.xmin/xStep)*xStep,yStart=Math.ceil(view.ymin/yStep)*yStep;
      for(let x=xStart,count=0;x<=view.xmax&&count<100;x+=xStep,count++){
        const X=px(x);svg.append(node("line",{x1:X,y1:pad.top,x2:X,y2:height-pad.bottom,class:"graph-grid"}));
        svg.append(node("text",{x:X,y:height-pad.bottom+22,"text-anchor":"middle",class:"graph-label"},fmt(x)));
      }
      for(let y=yStart,count=0;y<=view.ymax&&count<100;y+=yStep,count++){
        const Y=py(y);svg.append(node("line",{x1:pad.left,y1:Y,x2:width-pad.right,y2:Y,class:"graph-grid"}));
        svg.append(node("text",{x:pad.left-10,y:Y+4,"text-anchor":"end",class:"graph-label"},fmt(y)));
      }
      if(view.xmin<=0&&view.xmax>=0)svg.append(node("line",{x1:px(0),y1:pad.top,x2:px(0),y2:height-pad.bottom,class:"graph-axis"}));
      if(view.ymin<=0&&view.ymax>=0)svg.append(node("line",{x1:pad.left,y1:py(0),x2:width-pad.right,y2:py(0),class:"graph-axis"}));
      let d="",active=false,previous=null;
      sampled.forEach(p=>{
        if(!Number.isFinite(p.x)||!Number.isFinite(p.y)||p.x<view.xmin||p.x>view.xmax){active=false;previous=null;return;}
        if(previous&&Math.abs(p.y-previous.y)>(view.ymax-view.ymin)*.65)active=false;
        d+=(active?"L":"M")+px(p.x).toFixed(2)+","+py(p.y).toFixed(2)+" ";active=true;previous=p;
      });
      if(d){const clipId="graph-clip-"+Math.random().toString(36).slice(2);const defs=node("defs");const clip=node("clipPath",{id:clipId});clip.append(node("rect",{x:pad.left,y:pad.top,width:plotW,height:plotH}));defs.append(clip);svg.append(defs);const path=node("path",{d,class:"graph-curve","clip-path":`url(#${clipId})`});svg.append(path);}
      svg.append(node("text",{x:(pad.left+width-pad.right)/2,y:height-8,"text-anchor":"middle",class:"graph-axis-title"},"x"));
      svg.append(node("text",{x:16,y:height/2,transform:`rotate(-90 16 ${height/2})`,"text-anchor":"middle",class:"graph-axis-title"},"y"));
      if(selectedPoint&&selectedPoint.x>=view.xmin&&selectedPoint.x<=view.xmax&&selectedPoint.y>=view.ymin&&selectedPoint.y<=view.ymax){
        const sx=px(selectedPoint.x),sy=py(selectedPoint.y),label=`(${fmt(selectedPoint.x)}, ${fmt(selectedPoint.y)})`,lx=Math.min(width-pad.right-125,Math.max(pad.left+4,sx+10)),ly=Math.max(pad.top+18,sy-10);
        svg.append(node("line",{x1:sx,y1:pad.top,x2:sx,y2:height-pad.bottom,class:"graph-coordinate-guide"}),node("line",{x1:pad.left,y1:sy,x2:width-pad.right,y2:sy,class:"graph-coordinate-guide"}),node("circle",{cx:sx,cy:sy,r:5,class:"graph-coordinate-point"}),node("rect",{x:lx-4,y:ly-16,width:Math.min(125,label.length*7+10),height:23,rx:5,class:"graph-coordinate-label-bg"}),node("text",{x:lx+1,y:ly,"text-anchor":"start",class:"graph-coordinate-label"},label));
      }
    };
    svg.addEventListener("click",event=>{
      if(drag||pointers.size)return;
      const rect=svg.getBoundingClientRect(),sx=(event.clientX-rect.left)/rect.width*width,sy=(event.clientY-rect.top)/rect.height*height;
      if(sx<pad.left||sx>width-pad.right||sy<pad.top||sy>height-pad.bottom)return;
      let nearest=null,best=Infinity;
      sampled.forEach(p=>{if(!Number.isFinite(p.x)||!Number.isFinite(p.y))return;const dx=pad.left+(p.x-view.xmin)/(view.xmax-view.xmin)*plotW-sx,dy=pad.top+(view.ymax-p.y)/(view.ymax-view.ymin)*plotH-sy,d=dx*dx+dy*dy;if(d<best){best=d;nearest=p;}});
      if(nearest&&best<=Math.max(22,rect.width*.035)**2){selectedPoint={x:nearest.x,y:nearest.y};render();}
    });
    const zoomAt=(cx,cy,factor)=>{
      const xRatio=(cx-view.xmin)/(view.xmax-view.xmin),yRatio=(cy-view.ymin)/(view.ymax-view.ymin);
      const nextXSpan=Math.max(1e-8,Math.min(1e9,(view.xmax-view.xmin)*factor));
      const nextYSpan=nextXSpan*plotH/plotW;
      view.xmin=cx-xRatio*nextXSpan;view.xmax=view.xmin+nextXSpan;
      view.ymin=cy-yRatio*nextYSpan;view.ymax=view.ymin+nextYSpan;
      render();scheduleResample();
    };
    const pointAt=event=>{const rect=svg.getBoundingClientRect();return {x:view.xmin+(event.clientX-rect.left)/rect.width*(view.xmax-view.xmin),y:view.ymax-(event.clientY-rect.top)/rect.height*(view.ymax-view.ymin)};};
    svg.addEventListener("pointerdown",event=>{
      if(event.pointerType==="mouse"&&event.button!==0)return;
      event.preventDefault();svg.setPointerCapture(event.pointerId);pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});
      if(pointers.size===1)drag={x:event.clientX,y:event.clientY,xmin:view.xmin,xmax:view.xmax,ymin:view.ymin,ymax:view.ymax};
      else if(pointers.size===2){const ps=[...pointers.values()];lastPinch=Math.hypot(ps[0].x-ps[1].x,ps[0].y-ps[1].y);drag=null;}
    });
    svg.addEventListener("pointermove",event=>{
      if(!pointers.has(event.pointerId))return;
      const old=pointers.get(event.pointerId);pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});
      if(pointers.size>=2){
        const ps=[...pointers.values()],dist=Math.hypot(ps[0].x-ps[1].x,ps[0].y-ps[1].y);
        if(lastPinch>0&&dist>0){const rect=svg.getBoundingClientRect(),mx=(ps[0].x+ps[1].x)/2,my=(ps[0].y+ps[1].y)/2;zoomAt(view.xmin+(mx-rect.left)/rect.width*(view.xmax-view.xmin),view.ymax-(my-rect.top)/rect.height*(view.ymax-view.ymin),lastPinch/dist);}
        lastPinch=dist;return;
      }
      if(!drag)return;
      const rect=svg.getBoundingClientRect(),dx=(event.clientX-drag.x)/rect.width*(drag.xmax-drag.xmin),dy=(event.clientY-drag.y)/rect.height*(drag.ymax-drag.ymin);
      view.xmin=drag.xmin-dx;view.xmax=drag.xmax-dx;view.ymin=drag.ymin+dy;view.ymax=drag.ymax+dy;render();scheduleResample();
    });
    const endPointer=event=>{pointers.delete(event.pointerId);if(pointers.size<2)lastPinch=0;if(!pointers.size)drag=null;};
    svg.addEventListener("pointerup",endPointer);svg.addEventListener("pointercancel",endPointer);svg.addEventListener("lostpointercapture",endPointer);
    svg.addEventListener("wheel",event=>{event.preventDefault();const p=pointAt(event);zoomAt(p.x,p.y,event.deltaY<0?.82:1.22);},{passive:false});
    const makeControl=(label,aria,action)=>{const b=document.createElement("button");b.type="button";b.className="graph-control-button";b.textContent=label;b.setAttribute("aria-label",aria);b.addEventListener("click",action);controls.append(b);};
    makeControl("−","Zoom out",()=>zoomAt((view.xmin+view.xmax)/2,(view.ymin+view.ymax)/2,1.25));
    makeControl("+","Zoom in",()=>zoomAt((view.xmin+view.xmax)/2,(view.ymin+view.ymax)/2,.8));
    makeControl("Reset","Reset graph view",()=>{Object.assign(view,initialView);render();scheduleResample();});
    render();figure.append(controls,svg,caption);return figure;
  }
  function drawRelationGraph(segments,bounds={},relation=null) {
    const figure=document.createElement("figure");figure.className="graph-figure";
    const width=900,height=520,pad={left:68,right:24,top:24,bottom:54},plotW=width-pad.left-pad.right,plotH=height-pad.top-pad.bottom;
    if(!segments.length){const msg=document.createElement("figcaption");msg.textContent="No real curve was found in this viewing window. Try a wider x/y range.";figure.append(msg);return figure;}
    let xmin=Number(bounds.x_min),xmax=Number(bounds.x_max),ymin=Number(bounds.y_min),ymax=Number(bounds.y_max);
    if(![xmin,xmax,ymin,ymax].every(Number.isFinite)||xmin>=xmax||ymin>=ymax){xmin=-10;xmax=10;ymin=-10;ymax=10;}
    const cx=(xmin+xmax)/2,cy=(ymin+ymax)/2,scale=Math.max((xmax-xmin)/plotW,(ymax-ymin)/plotH);
    const xSpan=scale*plotW,ySpan=scale*plotH,view={xmin:cx-xSpan/2,xmax:cx+xSpan/2,ymin:cy-ySpan/2,ymax:cy+ySpan/2},initialView={...view};
    const svgNS="http://www.w3.org/2000/svg",svg=document.createElementNS(svgNS,"svg");
    svg.setAttribute("viewBox","0 0 "+width+" "+height);svg.setAttribute("role","img");
    svg.setAttribute("aria-label","Interactive implicit equation graph. Drag to pan; pinch or scroll to zoom.");svg.style.touchAction="none";
    const controls=document.createElement("div");controls.className="graph-controls";controls.setAttribute("aria-label","Graph controls");
    const caption=document.createElement("figcaption");caption.textContent="Drag to move the graph; pinch or scroll to zoom. Use +/− or Reset. The curve resamples as you move.";
    const node=(tag,attrs={},value)=>{const el=document.createElementNS(svgNS,tag);Object.entries(attrs).forEach(([k,v])=>el.setAttribute(k,String(v)));if(value!==undefined)el.textContent=value;return el;};
    const fmt=v=>Math.abs(v)<1e-9?"0":Math.abs(v)>=1e4||Math.abs(v)<1e-3?v.toExponential(1):Number(v.toPrecision(4)).toString();
    const niceStep=range=>{const raw=range/8,power=Math.pow(10,Math.floor(Math.log10(Math.max(raw,1e-12)))),fraction=raw/power;return(fraction<1.5?1:fraction<3.5?2:fraction<7.5?5:10)*power;};
    let currentSegments=segments,requestTimer=null,requestVersion=0,drag=null,lastPinch=0,selectedPoint=null;
    const pointers=new Map();
    const render=()=>{
      svg.replaceChildren();
      const px=x=>pad.left+(x-view.xmin)/(view.xmax-view.xmin)*plotW,py=y=>pad.top+(view.ymax-y)/(view.ymax-view.ymin)*plotH;
      const xs=niceStep(view.xmax-view.xmin),ys=niceStep(view.ymax-view.ymin);
      for(let x=Math.ceil(view.xmin/xs)*xs,count=0;x<=view.xmax&&count<100;x+=xs,count++){const X=px(x);svg.append(node("line",{x1:X,y1:pad.top,x2:X,y2:height-pad.bottom,class:"graph-grid"}));svg.append(node("text",{x:X,y:height-pad.bottom+22,"text-anchor":"middle",class:"graph-label"},fmt(x)));}
      for(let y=Math.ceil(view.ymin/ys)*ys,count=0;y<=view.ymax&&count<100;y+=ys,count++){const Y=py(y);svg.append(node("line",{x1:pad.left,y1:Y,x2:width-pad.right,y2:Y,class:"graph-grid"}));svg.append(node("text",{x:pad.left-10,y:Y+4,"text-anchor":"end",class:"graph-label"},fmt(y)));}
      if(view.xmin<=0&&view.xmax>=0)svg.append(node("line",{x1:px(0),y1:pad.top,x2:px(0),y2:height-pad.bottom,class:"graph-axis"}));
      if(view.ymin<=0&&view.ymax>=0)svg.append(node("line",{x1:pad.left,y1:py(0),x2:width-pad.right,y2:py(0),class:"graph-axis"}));
      let d="";
      currentSegments.forEach(q=>{if(![q.x1,q.y1,q.x2,q.y2].every(Number.isFinite))return;d+="M"+px(q.x1).toFixed(2)+","+py(q.y1).toFixed(2)+"L"+px(q.x2).toFixed(2)+","+py(q.y2).toFixed(2)+" ";});
      if(d){const clipId="relation-clip-"+Math.random().toString(36).slice(2),defs=node("defs"),clip=node("clipPath",{id:clipId});clip.append(node("rect",{x:pad.left,y:pad.top,width:plotW,height:plotH}));defs.append(clip);svg.append(defs,node("path",{d,class:"graph-curve","clip-path":"url(#"+clipId+")"}));}
      svg.append(node("text",{x:(pad.left+width-pad.right)/2,y:height-8,"text-anchor":"middle",class:"graph-axis-title"},"x"));
      svg.append(node("text",{x:16,y:height/2,transform:"rotate(-90 16 "+(height/2)+")","text-anchor":"middle",class:"graph-axis-title"},"y"));
      if(selectedPoint&&selectedPoint.x>=view.xmin&&selectedPoint.x<=view.xmax&&selectedPoint.y>=view.ymin&&selectedPoint.y<=view.ymax){
        const sx=px(selectedPoint.x),sy=py(selectedPoint.y),label="("+fmt(selectedPoint.x)+", "+fmt(selectedPoint.y)+")",lx=Math.min(width-pad.right-125,Math.max(pad.left+4,sx+10)),ly=Math.max(pad.top+18,sy-10);
        svg.append(node("line",{x1:sx,y1:pad.top,x2:sx,y2:height-pad.bottom,class:"graph-coordinate-guide"}),node("line",{x1:pad.left,y1:sy,x2:width-pad.right,y2:sy,class:"graph-coordinate-guide"}),node("circle",{cx:sx,cy:sy,r:5,class:"graph-coordinate-point"}),node("rect",{x:lx-4,y:ly-16,width:Math.min(125,label.length*7+10),height:23,rx:5,class:"graph-coordinate-label-bg"}),node("text",{x:lx+1,y:ly,"text-anchor":"start",class:"graph-coordinate-label"},label));
      }
    };
    svg.addEventListener("click",event=>{
      if(drag||pointers.size)return;
      const rect=svg.getBoundingClientRect(),sx=(event.clientX-rect.left)/rect.width*width,sy=(event.clientY-rect.top)/rect.height*height;
      if(sx<pad.left||sx>width-pad.right||sy<pad.top||sy>height-pad.bottom)return;
      let nearest=null,best=Infinity;
      currentSegments.forEach(q=>{if(![q.x1,q.y1,q.x2,q.y2].every(Number.isFinite))return;const ax=pad.left+(q.x1-view.xmin)/(view.xmax-view.xmin)*plotW,ay=pad.top+(view.ymax-q.y1)/(view.ymax-view.ymin)*plotH,bx=pad.left+(q.x2-view.xmin)/(view.xmax-view.xmin)*plotW,by=pad.top+(view.ymax-q.y2)/(view.ymax-view.ymin)*plotH,dx=bx-ax,dy=by-ay,den=dx*dx+dy*dy,t=den?Math.max(0,Math.min(1,((sx-ax)*dx+(sy-ay)*dy)/den)):0,pxs=ax+t*dx,pys=ay+t*dy,dist=(pxs-sx)**2+(pys-sy)**2;if(dist<best){best=dist;nearest={x:q.x1+t*(q.x2-q.x1),y:q.y1+t*(q.y2-q.y1)};}});
      if(nearest&&best<=Math.max(22,rect.width*.035)**2){selectedPoint=nearest;render();}
    });
    const scheduleResample=()=>{
      if(!relation)return;
      if(requestTimer!==null)clearTimeout(requestTimer);
      requestTimer=setTimeout(async()=>{
        const version=++requestVersion;
        try{const response=await api("/api/v1/graph/relation",{relation:relation,x_min:view.xmin,x_max:view.xmax,y_min:view.ymin,y_max:view.ymax,grid_size:100},{timeoutMs:10000});if(version!==requestVersion||!Array.isArray(response.segments))return;currentSegments=response.segments;caption.textContent="Coordinates stay true to scale. Drag to pan; pinch, scroll, or use +/− to zoom. The graph resamples as you move.";render();}
        catch(error){if(version===requestVersion)caption.textContent="Graph refresh failed: "+error.message+" The last valid curve is still shown.";}
      },140);
    };
    const zoomAt=(x,y,factor)=>{
      const xr=(x-view.xmin)/(view.xmax-view.xmin),yr=(y-view.ymin)/(view.ymax-view.ymin),nextX=Math.max(1e-7,Math.min(1e9,(view.xmax-view.xmin)*factor)),nextY=nextX*plotH/plotW;
      view.xmin=x-xr*nextX;view.xmax=view.xmin+nextX;view.ymin=y-yr*nextY;view.ymax=view.ymin+nextY;render();scheduleResample();
    };
    const pointAt=event=>{const rect=svg.getBoundingClientRect();return{x:view.xmin+(event.clientX-rect.left)/rect.width*(view.xmax-view.xmin),y:view.ymax-(event.clientY-rect.top)/rect.height*(view.ymax-view.ymin)};};
    svg.addEventListener("pointerdown",event=>{
      if(event.pointerType==="mouse"&&event.button!==0)return;event.preventDefault();try{svg.setPointerCapture(event.pointerId);}catch{}
      pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});
      if(pointers.size===1)drag={x:event.clientX,y:event.clientY,...view};else if(pointers.size===2){const p=[...pointers.values()];lastPinch=Math.hypot(p[0].x-p[1].x,p[0].y-p[1].y);drag=null;}
    });
    svg.addEventListener("pointermove",event=>{
      if(!pointers.has(event.pointerId))return;pointers.set(event.pointerId,{x:event.clientX,y:event.clientY});
      if(pointers.size>=2){const p=[...pointers.values()],distance=Math.hypot(p[0].x-p[1].x,p[0].y-p[1].y);if(lastPinch>0&&distance>0){const rect=svg.getBoundingClientRect(),mx=(p[0].x+p[1].x)/2,my=(p[0].y+p[1].y)/2;zoomAt(view.xmin+(mx-rect.left)/rect.width*(view.xmax-view.xmin),view.ymax-(my-rect.top)/rect.height*(view.ymax-view.ymin),lastPinch/distance);}lastPinch=distance;return;}
      if(!drag)return;const rect=svg.getBoundingClientRect(),dx=(event.clientX-drag.x)/rect.width*(drag.xmax-drag.xmin),dy=(event.clientY-drag.y)/rect.height*(drag.ymax-drag.ymin);
      view.xmin=drag.xmin-dx;view.xmax=drag.xmax-dx;view.ymin=drag.ymin+dy;view.ymax=drag.ymax+dy;render();scheduleResample();
    });
    const endPointer=event=>{pointers.delete(event.pointerId);if(pointers.size<2)lastPinch=0;if(!pointers.size)drag=null;};
    svg.addEventListener("pointerup",endPointer);svg.addEventListener("pointercancel",endPointer);svg.addEventListener("lostpointercapture",endPointer);
    svg.addEventListener("wheel",event=>{event.preventDefault();const p=pointAt(event);zoomAt(p.x,p.y,event.deltaY<0?.82:1.22);},{passive:false});
    const addControl=(label,aria,action)=>{const b=document.createElement("button");b.type="button";b.className="graph-control-button";b.textContent=label;b.setAttribute("aria-label",aria);b.addEventListener("click",action);controls.append(b);};
    addControl("−","Zoom out",()=>zoomAt((view.xmin+view.xmax)/2,(view.ymin+view.ymax)/2,1.25));
    addControl("+","Zoom in",()=>zoomAt((view.xmin+view.xmax)/2,(view.ymin+view.ymax)/2,.8));
    addControl("Reset","Reset graph view",()=>{Object.assign(view,initialView);render();scheduleResample();});
    render();figure.append(controls,svg,caption);return figure;
  }
  function equationGraphExpression(raw) {
    const normalized=String(raw).replaceAll("²","^2").replaceAll("³","^3").replace(/[−–]/g,"-").replace(/[×·]/g,"*").replaceAll("÷","/");
    const parts=normalized.split("=");if(parts.length>2||!parts[0]?.trim())return null;
    // Preserve the complete x-y curve (including both parabola branches).
    // If a third variable is present, graph the z=0 cross-section.
    const hasY=/\by\b/i.test(normalized);
    if(hasY)return {relation:normalized.replace(/\bz\b/gi,"0")};
    const expression=(parts.length===2?"("+parts[0]+")-("+parts[1]+")":parts[0]).replace(/\bz\b/gi,"0");
    if(!/^[0-9xX+*/^().\s-]+$/.test(expression))return null;
    return expression;
  }
  async function appendEquationGraph(container,form,result) {
    const mode=val(form,"equation_mode");
    const section=document.createElement("section");section.className="equation-graph-section";
    const heading=document.createElement("h3");heading.textContent="Equation graph";section.append(heading);
    const note=document.createElement("p");note.className="field-help";
    note.textContent=["linear","quadratic"].includes(mode)
      ?"The graph uses an automatic viewing range. You do not need to enter minimum or maximum values."
      :mode==="system"
      ?"The graph shows the first equation as a 2D slice; a full system may require multiple plots."
      :"The full x-y relation is plotted, including both branches of parabolas; z is fixed at 0 when present.";
    section.append(note);container.append(section);
    if(mode==="binomial"){
      const message=document.createElement("p");message.className="field-help";
      message.textContent="A binomial expansion is an expression rather than an equation. Convert it into an equation to plot it.";
      section.append(message);return;
    }
    let raw=val(form,"equation");
    if(mode==="system")raw=val(form,"system_equations").split(/\n+/).map(line=>line.trim()).filter(Boolean)[0]||"";
    const graphExpression=equationGraphExpression(raw);
    if(!graphExpression){const msg=document.createElement("p");msg.className="field-help";msg.textContent="This equation could not be plotted with the current 2D graph engine. The equation result is still available above.";section.append(msg);return;}
    let x_min,x_max;
    try{x_min=number(form,"graph_x_min");x_max=number(form,"graph_x_max");}
    catch{ x_min=-10; x_max=10; }
    if(!Number.isFinite(x_min)||!Number.isFinite(x_max)||x_min>=x_max){x_min=-10;x_max=10;}
    try{
      if(graphExpression.relation){const bounds={x_min,x_max,y_min:-10,y_max:10};const sampled=await api("/api/v1/graph/relation",{relation:graphExpression.relation,...bounds,grid_size:100});if(Array.isArray(sampled.segments)&&sampled.segments.length){section.append(drawRelationGraph(sampled.segments,bounds,graphExpression.relation));const caption=document.createElement("p");caption.className="field-help";caption.textContent="The complete 2D relation is plotted, including both branches where present.";section.append(caption);}else{const msg=document.createElement("p");msg.className="field-help";msg.textContent="No visible curve segments were found in this viewing range.";section.append(msg);}return;}
      const expression=graphExpression;
      const sampled=await api("/api/v1/graph/sample",{expression,x_min,x_max,points:401});
      if(Array.isArray(sampled.points)&&sampled.points.length) {
        section.append(drawGraph(sampled.points,{expression,xMin:x_min,xMax:x_max}));
        const caption=document.createElement("p");caption.className="field-help";caption.textContent="x range: "+x_min+" to "+x_max+". Zeros of the plotted residual indicate solutions in this slice.";section.append(caption);
      } else {
        const msg=document.createElement("p");msg.className="field-help";msg.textContent="No graph samples were returned. The equation result is still available above.";section.append(msg);
      }
    }catch(error){const msg=document.createElement("p");msg.className="field-help";msg.textContent="Graph unavailable for this equation: "+error.message;section.append(msg);}
  }
  function transformDegreeTrig(expression) {
    expression=expression.replace(/π/g,"pi");
    expression=expression.replace(/\b(sin|cos|tan|sec|csc|cosec|cot)\s+([+-]?(?:\d+(?:\.\d*)?|\.\d+))\b/gi,"$1($2)");
    if(angleMode!=="DEG")return expression;
    const names=new Set(["sin","cos","tan","sec","csc","cosec","cot"]);
    const inverseNames=new Set(["asin","acos","atan"]);
    let out="",i=0;
    while(i<expression.length){
      const match=expression.slice(i).match(/^([A-Za-z_][A-Za-z_0-9]*)\s*\(/);
      if(!match){out+=expression[i++];continue;}
      const name=match[1],normalizedName=name.toLowerCase(),open=i+match[0].lastIndexOf("(");
      let depth=1,j=open+1;
      while(j<expression.length&&depth>0){if(expression[j]==="(")depth++;else if(expression[j]===")")depth--;j++;}
      if(depth!==0){out+=expression.slice(i);break;}
      const inner=transformDegreeTrig(expression.slice(open+1,j-1));
      if(names.has(normalizedName))out+=name+"(radians("+inner+"))";
      else if(inverseNames.has(normalizedName))out+="degrees("+name+"("+inner+"))";
      else out+=name+"("+inner+")";
      i=j;
    }
    return out;
  }
  function setAngleMode(mode){angleMode=mode;angleButtons.forEach(btn=>{const selected=btn.dataset.angle===mode;btn.classList.toggle("is-selected",selected);btn.setAttribute("aria-pressed",String(selected));});}
  angleButtons.forEach(btn=>btn.addEventListener("click",()=>setAngleMode(btn.dataset.angle)));
  function loadHistory(){try{const value=JSON.parse(localStorage.getItem(HISTORY_KEY)||"[]");return Array.isArray(value)?value.filter(item=>item&&typeof item.expression==="string"&&typeof item.displayedResult==="string").slice(0,20):[];}catch{return[];}}
  function saveHistory(item){history=[item,...history].slice(0,20);try{localStorage.setItem(HISTORY_KEY,JSON.stringify(history));}catch{}}
  function formatNumber(value){return typeof value==="number"&&Number.isFinite(value)?value.toLocaleString("en-US",{maximumSignificantDigits:12}):String(value);}
  function historySection(){
    const section=document.createElement("section");section.className="history-mini";const h=document.createElement("h3");h.textContent="Recent calculations";section.append(h);
    if(!history.length){const p=document.createElement("p");p.className="muted";p.textContent="No saved calculations in this browser yet.";section.append(p);return section;}
    history.slice(0,8).forEach(item=>{const row=document.createElement("div");row.className="history-mini-row";const reuse=button(item.expression,"history-expression","button");reuse.addEventListener("click",()=>{const input=$('[name="expression"]');if(input){input.value=item.expression;input.focus();}});const result=document.createElement("strong");result.textContent=item.displayedResult;row.append(reuse,result);section.append(row);});
    const clear=button("Clear history","secondary-button","button");clear.addEventListener("click",()=>{if(window.confirm("Clear recent calculations stored in this browser?")){history=[];try{localStorage.removeItem(HISTORY_KEY);}catch{}renderTool(activeTool);}});section.append(clear);return section;
  }
  const formulaReferences = {
    "Scientific Calculator": {
      intro:"Core algebra, trigonometry, logarithms, exponentials, powers, roots, and angle conversions.",
      items:[
        ["Angle conversion","180° = π rad; θ(rad) = θ(deg) × π/180; θ(deg) = θ(rad) × 180/π"],
        ["Basic ratios","sin θ = opposite/hypotenuse; cos θ = adjacent/hypotenuse; tan θ = opposite/adjacent"],
        ["Reciprocal ratios","cosec θ = 1/sin θ; sec θ = 1/cos θ; cot θ = 1/tan θ"],
        ["Quotient identities","tan θ = sin θ/cos θ; cot θ = cos θ/sin θ"],
        ["Pythagorean identities","sin²θ + cos²θ = 1; 1 + tan²θ = sec²θ; 1 + cot²θ = cosec²θ"],
        ["Even and odd identities","sin(−θ)=−sin θ; cos(−θ)=cos θ; tan(−θ)=−tan θ"],
        ["Co-function identities","sin(π/2−θ)=cos θ; cos(π/2−θ)=sin θ; tan(π/2−θ)=cot θ"],
        ["Periodicity","sin(θ+2π)=sin θ; cos(θ+2π)=cos θ; tan(θ+π)=tan θ"],
        ["Addition: sine","sin(A±B)=sin A cos B ± cos A sin B"],
        ["Addition: cosine","cos(A±B)=cos A cos B ∓ sin A sin B"],
        ["Addition: tangent","tan(A±B)=(tan A ± tan B)/(1 ∓ tan A tan B)"],
        ["Double angle","sin 2A=2 sin A cos A; cos 2A=cos²A−sin²A=1−2sin²A=2cos²A−1"],
        ["Tangent double angle","tan 2A=2 tan A/(1−tan²A)"],
        ["Half-angle identities","sin²(A/2)=(1−cos A)/2; cos²(A/2)=(1+cos A)/2"],
        ["Product-to-sum","2 sin A cos B=sin(A+B)+sin(A−B)"],
        ["Sine product","2 sin A sin B=cos(A−B)−cos(A+B)"],
        ["Cosine product","2 cos A cos B=cos(A+B)+cos(A−B)"],
        ["Sum-to-product","sin A+sin B=2 sin((A+B)/2) cos((A−B)/2)"],
        ["Cosine sum-to-product","cos A+cos B=2 cos((A+B)/2) cos((A−B)/2)"],
        ["Special angles","sin 0=0; sin π/6=1/2; sin π/4=√2/2; sin π/3=√3/2; sin π/2=1"],
        ["Special cosine values","cos 0=1; cos π/6=√3/2; cos π/4=√2/2; cos π/3=1/2; cos π/2=0"],
        ["Special tangent values","tan 0=0; tan π/6=1/√3; tan π/4=1; tan π/3=√3; tan π/2 is undefined"],
        ["Inverse trig ranges","arcsin x ∈ [−π/2,π/2]; arccos x ∈ [0,π]; arctan x ∈ (−π/2,π/2)"],
        ["Logarithm product and quotient","logₐ(xy)=logₐx+logₐy; logₐ(x/y)=logₐx−logₐy"],
        ["Logarithm power and change of base","logₐ(xⁿ)=n logₐx; logₐx=log_bx/log_ba"],
        ["Logarithm identities","logₐ1=0; logₐa=1; a^(logₐx)=x"],
        ["Exponent laws","aᵐaⁿ=aᵐ⁺ⁿ; aᵐ/aⁿ=aᵐ⁻ⁿ; (aᵐ)ⁿ=aᵐⁿ"],
        ["Zero and negative powers","a⁰=1 (a≠0); a⁻ⁿ=1/aⁿ"],
        ["Fractional powers","a^(m/n)=ⁿ√(aᵐ) where defined; √(ab)=√a√b for a,b≥0"],
        ["Quadratic formula","For ax²+bx+c=0: x=(−b±√(b²−4ac))/(2a), a≠0"],
        ["Arithmetic sequence","aₙ=a₁+(n−1)d; Sₙ=n(a₁+aₙ)/2"],
        ["Geometric sequence","aₙ=a₁rⁿ⁻¹; Sₙ=a₁(1−rⁿ)/(1−r), r≠1"],
        ["Infinite geometric series","S∞=a₁/(1−r), when |r|<1"],
        ["Factorial and combinations","n!=n(n−1)…1; ⁿCᵣ=n!/[r!(n−r)!]"]
      ]
    },
    "Equations": {
      intro:"Standard formulas for linear and quadratic equations, polynomials, inequalities, identities, and binomial expansion.",
      items:[
        ["Linear equation","ax+b=0 ⇒ x=−b/a, a≠0"],
        ["Two-variable linear equation","ax+by=c; if (a,b)≠(0,0), its graph is a straight line"],
        ["Slope-intercept form","y=mx+c; point-slope form: y−y₁=m(x−x₁)"],
        ["Quadratic standard form","ax²+bx+c=0, a≠0"],
        ["Quadratic formula","x=(−b±√D)/(2a), where D=b²−4ac"],
        ["Discriminant","D>0: two distinct real roots; D=0: equal real roots; D<0: complex-conjugate roots"],
        ["Sum and product of roots","α+β=−b/a; αβ=c/a"],
        ["Vertex of a quadratic","For y=ax²+bx+c: xᵥ=−b/(2a), yᵥ=f(−b/(2a))"],
        ["Completing the square","x²+px+q=(x+p/2)²+q−p²/4"],
        ["Difference of squares","a²−b²=(a−b)(a+b)"],
        ["Square of a sum/difference","(a±b)²=a²±2ab+b²"],
        ["Sum and difference of cubes","a³+b³=(a+b)(a²−ab+b²); a³−b³=(a−b)(a²+ab+b²)"],
        ["Cube of a sum/difference","(a±b)³=a³±3a²b+3ab²±b³"],
        ["Factor theorem","If f(a)=0, then (x−a) is a factor of f(x)"],
        ["Remainder theorem","Remainder on division of f(x) by (x−a) is f(a)"],
        ["Polynomial division","f(x)=g(x)q(x)+r(x), where deg r < deg g"],
        ["Binomial theorem","(a+b)ⁿ=Σᵣ₌₀ⁿ ⁿCᵣaⁿ⁻ʳbʳ"],
        ["Binomial coefficients","ⁿCᵣ=ⁿCₙ₋ᵣ; ⁿCᵣ+ⁿCᵣ₋₁=ⁿ⁺¹Cᵣ"],
        ["Absolute value","|x|=x for x≥0; |x|=−x for x<0"],
        ["Proportions","a/b=c/d ⇒ ad=bc, when denominators are non-zero"],
        ["Direct and inverse variation","y=kx; y=k/x (x≠0)"],
        ["Linear system (2×2)","a₁x+b₁y=c₁; a₂x+b₂y=c₂; solve if determinant a₁b₂−a₂b₁≠0"],
        ["Cramer's rule (2×2)","Δ=a₁b₂−a₂b₁; x=(c₁b₂−c₂b₁)/Δ; y=(a₁c₂−a₂c₁)/Δ, Δ≠0"],
        ["Exponent equation","aˣ=aʸ ⇒ x=y when a>0 and a≠1"],
        ["Logarithmic equation","logₐx=y ⇔ aʸ=x, with a>0, a≠1, x>0"]
      ]
    },
    "Graphing Calculator": {
      intro:"Equations and properties for common function graphs, transformations, intercepts, and conic sections.",
      items:[
        ["Straight line","y=mx+c; slope m; y-intercept c"],
        ["Slope between points","m=(y₂−y₁)/(x₂−x₁), x₂≠x₁"],
        ["Point-to-point distance","d=√((x₂−x₁)²+(y₂−y₁)²)"],
        ["Midpoint","M=((x₁+x₂)/2,(y₁+y₂)/2)"],
        ["Quadratic graph","y=ax²+bx+c, a≠0; vertex x=−b/(2a)"],
        ["Parabola vertex form","y=a(x−h)²+k; vertex (h,k)"],
        ["Circle","(x−h)²+(y−k)²=r²; centre (h,k), radius r"],
        ["Ellipse","(x−h)²/a²+(y−k)²/b²=1"],
        ["Hyperbola","(x−h)²/a²−(y−k)²/b²=1"],
        ["Absolute value","y=|x|; translated form y=a|x−h|+k"],
        ["Reciprocal","y=1/x, x≠0; translated form y=a/(x−h)+k"],
        ["Exponential","y=abˣ; for b>0, b≠1"],
        ["Logarithmic","y=log_b x, x>0, b>0, b≠1"],
        ["Sine and cosine periods","sin(bx), cos(bx): period 2π/|b| radians"],
        ["Tangent period","tan(bx): period π/|b| radians"],
        ["Sine transformation","y=A sin(B(x−C))+D; amplitude |A|, period 2π/|B|"],
        ["Cosine transformation","y=A cos(B(x−C))+D; amplitude |A|, period 2π/|B|"],
        ["Function transformations","y=f(x−h)+k shifts right h and up k"],
        ["Even and odd functions","Even: f(−x)=f(x); odd: f(−x)=−f(x)"],
        ["Intercepts","x-intercepts satisfy f(x)=0; y-intercept is f(0), when defined"],
        ["Domain and range","Domain: allowed x-values; range: resulting y-values"]
      ]
    },
    "Calculus": {
      intro:"Core limits, continuity, differentiation rules, standard derivatives, integration rules, and standard antiderivatives. Trigonometric derivative and integral formulas use radians.",
      items:[
        ["Derivative definition","f′(x)=limₕ→₀ [f(x+h)−f(x)]/h, when the limit exists"],
        ["Constant and power rules","d(c)/dx=0; d(xⁿ)/dx=nxⁿ⁻¹"],
        ["Constant multiple and sum","(cf)'=cf'; (f±g)'=f'±g'"],
        ["Product rule","(uv)'=u'v+uv'"],
        ["Quotient rule","(u/v)'=(u'v−uv')/v², v≠0"],
        ["Chain rule","d f(g(x))/dx=f'(g(x))g'(x)"],
        ["Exponential derivatives","d(eˣ)/dx=eˣ; d(aˣ)/dx=aˣ ln a"],
        ["Logarithmic derivatives","d(ln|x|)/dx=1/x; d(logₐx)/dx=1/(x ln a)"],
        ["Trigonometric derivatives","(sin x)'=cos x; (cos x)'=−sin x; (tan x)'=sec²x"],
        ["More trig derivatives","(cot x)'=−cosec²x; (sec x)'=sec x tan x; (cosec x)'=−cosec x cot x"],
        ["Inverse trig derivatives","(arcsin x)'=1/√(1−x²); (arccos x)'=−1/√(1−x²)"],
        ["More inverse trig derivatives","(arctan x)'=1/(1+x²); (arccot x)'=−1/(1+x²) on the usual principal branch"],
        ["Hyperbolic derivatives","(sinh x)'=cosh x; (cosh x)'=sinh x; (tanh x)'=sech²x"],
        ["Implicit differentiation","For F(x,y)=0: dy/dx=−Fₓ/Fᵧ when Fᵧ≠0"],
        ["Second derivative","f''(x)=d²f/dx²"],
        ["Critical points","Critical points occur where f'=0 or f' is undefined inside the domain"],
        ["Integration constant","∫f(x)dx=F(x)+C where F'(x)=f(x)"],
        ["Power integral","∫xⁿdx=xⁿ⁺¹/(n+1)+C, n≠−1"],
        ["Reciprocal integral","∫dx/x=ln|x|+C"],
        ["Exponential integrals","∫eˣdx=eˣ+C; ∫aˣdx=aˣ/ln a+C, a>0, a≠1"],
        ["Sine and cosine integrals","∫sin x dx=−cos x+C; ∫cos x dx=sin x+C"],
        ["Tangent and cotangent integrals","∫tan x dx=−ln|cos x|+C; ∫cot x dx=ln|sin x|+C"],
        ["Secant and cosecant integrals","∫sec²x dx=tan x+C; ∫cosec²x dx=−cot x+C"],
        ["Secant tangent integrals","∫sec x tan x dx=sec x+C; ∫cosec x cot x dx=−cosec x+C"],
        ["Logarithmic integral","∫ln x dx=x ln x−x+C, x>0"],
        ["Inverse tangent integral","∫dx/(1+x²)=arctan x+C"],
        ["Inverse sine integral","∫dx/√(1−x²)=arcsin x+C"],
        ["Basic rational integral","∫dx/(a²+x²)=(1/a)arctan(x/a)+C, a>0"],
        ["Basic radical integral","∫dx/√(a²−x²)=arcsin(x/a)+C, a>0"],
        ["Linearity of integration","∫(af(x)±bg(x))dx=a∫f(x)dx±b∫g(x)dx"],
        ["Substitution rule","If u=g(x), then ∫f(g(x))g'(x)dx=∫f(u)du"],
        ["Integration by parts","∫u dv=uv−∫v du"],
        ["Definite integral","∫ₐᵇf(x)dx=F(b)−F(a), where F'=f"],
        ["Reversing limits","∫ₐᵇf(x)dx=−∫ᵦₐf(x)dx; ∫ₐᵃf(x)dx=0"],
        ["Symmetry of integrals","For even f: ∫₋ₐᵃf(x)dx=2∫₀ᵃf(x)dx; for odd f, the integral is 0"],
        ["Fundamental limits","limₓ→₀ sin x/x=1; limₓ→₀ (1−cos x)/x²=1/2"],
        ["L'Hôpital's rule","For indeterminate 0/0 or ∞/∞ forms, lim f/g=lim f'/g' when the rule's conditions hold"]
      ]
    },
    "Matrix Calculator": {
      intro:"Matrix operations, determinants, inverses, rank, transpose, and linear-system formulas.",
      items:[
        ["Addition and subtraction","(A±B)ᵢⱼ=Aᵢⱼ±Bᵢⱼ; A and B must have equal dimensions"],
        ["Scalar multiplication","(kA)ᵢⱼ=kAᵢⱼ"],
        ["Matrix multiplication","(AB)ᵢⱼ=Σₖ AᵢₖBₖⱼ; columns of A must equal rows of B"],
        ["Transpose","(Aᵀ)ᵢⱼ=Aⱼᵢ; (A+B)ᵀ=Aᵀ+Bᵀ"],
        ["Transpose of product","(AB)ᵀ=BᵀAᵀ"],
        ["Identity and zero matrices","AI=IA=A; A+O=A when dimensions are compatible"],
        ["2×2 determinant","det([[a,b],[c,d]])=ad−bc"],
        ["3×3 determinant","det(A)=a(ei−fh)−b(di−fg)+c(dh−eg) for rows [a,b,c],[d,e,f],[g,h,i]"],
        ["Determinant properties","det(AB)=det(A)det(B); det(Aᵀ)=det(A); det(I)=1"],
        ["Singular matrix","A is singular iff det(A)=0 for a square matrix"],
        ["2×2 inverse","A⁻¹=(1/(ad−bc))[[d,−b],[−c,a]], when ad−bc≠0"],
        ["Inverse properties","AA⁻¹=A⁻¹A=I; (AB)⁻¹=B⁻¹A⁻¹ when both inverses exist"],
        ["Transpose inverse","(Aᵀ)⁻¹=(A⁻¹)ᵀ when A is invertible"],
        ["Adjugate inverse","A⁻¹=adj(A)/det(A), when det(A)≠0"],
        ["Matrix powers","A⁰=I; AᵐAⁿ=Aᵐ⁺ⁿ for powers of the same square matrix"],
        ["Trace","tr(A)=Σᵢ Aᵢᵢ; tr(A+B)=tr(A)+tr(B)"],
        ["Rank","rank(A) is the number of pivots in row-echelon form"],
        ["Linear system","Ax=b; if A is invertible, x=A⁻¹b"],
        ["Cramer's rule","For Ax=b with det(A)≠0, xᵢ=det(Aᵢ)/det(A), where Aᵢ replaces column i by b"],
        ["Eigenvalue equation","Av=λv for nonzero vector v; det(A−λI)=0 gives eigenvalues"]
      ]
    },
    "Statistics": {
      intro:"Formulas for descriptive statistics, grouped data, spread, position, covariance, and correlation.",
      items:[
        ["Arithmetic mean","x̄=Σxᵢ/n"],
        ["Weighted mean","x̄w=Σwᵢxᵢ/Σwᵢ, when Σwᵢ≠0"],
        ["Median position","For ordered data: middle value when n is odd; average of positions n/2 and n/2+1 when n is even"],
        ["Range","R=xmax−xmin"],
        ["Population variance","σ²=Σ(xᵢ−μ)²/N"],
        ["Sample variance","s²=Σ(xᵢ−x̄)²/(n−1), n>1"],
        ["Standard deviation","σ=√σ²; s=√s²"],
        ["Coefficient of variation","CV=(standard deviation/mean)×100%, when mean is non-zero"],
        ["Grouped-data mean","x̄=Σfᵢxᵢ/Σfᵢ"],
        ["Quartiles and IQR","IQR=Q₃−Q₁"],
        ["Population covariance","Cov(X,Y)=Σ(xᵢ−μₓ)(yᵢ−μᵧ)/N"],
        ["Sample covariance","sₓᵧ=Σ(xᵢ−x̄)(yᵢ−ȳ)/(n−1)"],
        ["Pearson correlation","r=Cov(X,Y)/(sₓsᵧ), when both standard deviations are non-zero"],
        ["Probability from frequency","Relative frequency=f/N"],
        ["Z-score","z=(x−μ)/σ, σ>0"],
        ["Empirical rule","For approximately normal data: about 68%, 95%, and 99.7% lie within 1, 2, and 3 standard deviations"]
      ]
    },
    "Probability & Combinatorics": {
      intro:"Core counting rules, probability laws, conditional probability, permutations, combinations, and standard distributions.",
      items:[
        ["Probability bounds","0≤P(A)≤1; P(S)=1; P(∅)=0"],
        ["Complement","P(Aᶜ)=1−P(A)"],
        ["Addition rule","P(A∪B)=P(A)+P(B)−P(A∩B)"],
        ["Mutually exclusive events","If A∩B=∅, P(A∪B)=P(A)+P(B)"],
        ["Conditional probability","P(A|B)=P(A∩B)/P(B), P(B)>0"],
        ["Multiplication rule","P(A∩B)=P(A|B)P(B)"],
        ["Independent events","P(A∩B)=P(A)P(B)"],
        ["Bayes' theorem","P(Aᵢ|B)=P(B|Aᵢ)P(Aᵢ)/ΣⱼP(B|Aⱼ)P(Aⱼ)"],
        ["Factorial","n!=n(n−1)…2·1; 0!=1"],
        ["Permutations","ⁿPᵣ=n!/(n−r)!, 0≤r≤n"],
        ["Combinations","ⁿCᵣ=n!/[r!(n−r)!]"],
        ["Circular permutations","(n−1)! for n distinct objects arranged around a circle"],
        ["Permutations with repetition","Number of length-r sequences from n choices = nʳ"],
        ["Multinomial arrangements","n!/(n₁!n₂!…nₖ!), where Σnᵢ=n"],
        ["Binomial distribution","P(X=k)=ⁿCₖpᵏ(1−p)ⁿ⁻ᵏ"],
        ["Binomial mean and variance","E[X]=np; Var(X)=np(1−p)"],
        ["Expected value","E[X]=ΣxᵢP(X=xᵢ)"],
        ["Variance of a random variable","Var(X)=E[X²]−(E[X])²"],
        ["Addition principle","For disjoint choices, total ways = sum of the individual counts"],
        ["Multiplication principle","For successive independent choices, total outcomes = product of the number of choices"]
      ]
    },
    "Unit Converter": {
      intro:"Common metric, imperial, time, area, volume, speed, and temperature conversion relationships.",
      items:[
        ["Length","1 km=1000 m; 1 m=100 cm; 1 cm=10 mm; 1 in=2.54 cm"],
        ["Length: imperial","1 ft=12 in; 1 yd=3 ft; 1 mi=5280 ft"],
        ["Mass","1 t=1000 kg; 1 kg=1000 g; 1 g=1000 mg; 1 lb≈0.45359237 kg"],
        ["Time","1 min=60 s; 1 h=3600 s; 1 day=24 h; 1 week=7 days"],
        ["Area","1 m²=10,000 cm²; 1 km²=1,000,000 m²; 1 ha=10,000 m²"],
        ["Volume","1 m³=1000 L; 1 L=1000 mL; 1 mL=1 cm³"],
        ["US customary volume","1 US gal≈3.78541 L; 1 US qt≈0.946353 L"],
        ["Speed","1 m/s=3.6 km/h; 1 mph≈1.60934 km/h"],
        ["Temperature: Celsius/Fahrenheit","°F=(°C×9/5)+32; °C=(°F−32)×5/9"],
        ["Temperature: Kelvin","K=°C+273.15; °C=K−273.15"],
        ["Energy","1 cal≈4.184 J; 1 kWh=3.6×10⁶ J"],
        ["Pressure","1 bar=100,000 Pa; 1 atm≈101,325 Pa"],
        ["General linear conversion","target value = source value × conversion factor"]
      ]
    },
    "Finance & Loan EMI": {
      intro:"Common formulas for interest, compound growth, loan repayments, and repayment totals. Rates and periods must use consistent units.",
      items:[
        ["Simple interest","SI=Prt/100, where r is annual percent rate and t is years"],
        ["Simple-interest amount","A=P(1+rt/100)"],
        ["Compound amount","A=P(1+r/(100m))^(mt), m compounding periods per year"],
        ["Effective annual rate","EAR=(1+r/m)^m−1, where r is the annual rate as a decimal"],
        ["Monthly rate","i=annual nominal rate/12, expressed as a decimal"],
        ["Loan EMI","EMI=Pi(1+i)^n/[(1+i)^n−1], i>0"],
        ["Zero-interest EMI","EMI=P/n"],
        ["Total repayment","Total=EMI×n"],
        ["Total interest paid","Total interest=total repayment−principal"],
        ["Future value of regular deposits","FV=PMT[((1+i)^n−1)/i], for end-of-period deposits and i≠0"],
        ["Present value of an annuity","PV=PMT[1−(1+i)^−n]/i, i≠0"],
        ["Compound growth rate","A=P(1+i)^n"]
      ]
    },
    "Discount & GST Calculator": {
      intro:"Formulas for percentage discounts, markups, GST-exclusive prices, and GST-inclusive prices.",
      items:[
        ["Discount amount","D=marked price×discount rate/100"],
        ["Price after discount","SP=marked price−D"],
        ["Discount percentage","Discount %=D/marked price×100%, when marked price≠0"],
        ["Markup amount","Markup=cost×markup rate/100"],
        ["GST amount on taxable value","GST=taxable value×GST rate/100"],
        ["Total with GST added","Total=taxable value×(1+GST rate/100)"],
        ["GST included in total","GST portion=total×GST rate/(100+GST rate)"],
        ["Taxable value from GST-inclusive total","Taxable value=total×100/(100+GST rate)"],
        ["Equal CGST and SGST split","CGST=SGST=total GST/2, when the applicable intra-state GST is split equally"],
        ["Final price after discount then GST","Final=marked price×(1−discount rate/100)×(1+GST rate/100)"]
      ]
    },
    "BMI Calculator": {
      intro:"Formula definitions only. BMI is a screening measure and does not diagnose health conditions.",
      items:[
        ["Body mass index","BMI=weight (kg)/[height (m)]²"],
        ["Height conversion","height (m)=height (cm)/100"],
        ["Weight from BMI and height","weight (kg)=BMI×[height (m)]²"],
        ["Height from BMI and weight","height (m)=√[weight (kg)/BMI], for BMI>0"],
        ["Adult BMI category ranges","Underweight: <18.5; healthy-weight range: 18.5–24.9; overweight: 25.0–29.9; obesity: ≥30; categories are screening ranges"]
      ]
    },
    "Date Calculator": {
      intro:"Calendar and date-arithmetic rules, including leap years and elapsed-time calculations.",
      items:[
        ["Elapsed date difference","Elapsed days=absolute difference between the two calendar dates"],
        ["Add or subtract days","Result date=start date±number of calendar days"],
        ["Leap-year rule","Leap year if divisible by 400, or divisible by 4 but not by 100"],
        ["Days in a year","365 days in a common year; 366 days in a leap year"],
        ["Days in months","31: Jan, Mar, May, Jul, Aug, Oct, Dec; 30: Apr, Jun, Sep, Nov; Feb: 28 or 29"],
        ["Time difference","Elapsed duration=end date/time−start date/time, accounting for the selected time zone when relevant"],
        ["Inclusive day count","Inclusive days=elapsed day difference+1 when both endpoints are counted"]
      ]
    }
  };
  function formulaReferenceCard(title) {
    const data = formulaReferences[title];
    if (!data) return null;
    const section = document.createElement("section");
    section.className = "panel formula-sheet";
    section.setAttribute("aria-label", title + " formula sheet");
    const heading = document.createElement("div");
    heading.className = "panel-heading formula-sheet-heading";
    const titleNode = document.createElement("h2");
    titleNode.textContent = "Formula Sheet";
    const subtitle = document.createElement("p");
    subtitle.className = "formula-sheet-subtitle";
    subtitle.textContent = "Core formulas, arranged like clear textbook notes.";
    heading.append(titleNode, subtitle);
    const content = document.createElement("div");
    content.className = "formula-sheet-content";
    data.items.forEach(([name, formula]) => {
      const group = document.createElement("section");
      group.className = "formula-topic";
      const topic = document.createElement("h3");
      topic.textContent = name;
      group.append(topic);
      formula.split(/;\s*/).map(part => part.trim()).filter(Boolean).forEach(part => {
        const line = document.createElement("p");
        line.className = "formula-equation";
        line.textContent = part;
        group.append(line);
      });
      content.append(group);
    });
    section.append(heading, content);
    return section;
  }

  function scientificWorkspace(){
    angleToggle.hidden=false;
    const {form,body,output}=createPanel("Scientific Calculator","Type an expression or use the keypad. Evaluation is handled by the Python engine.");
    const expr=txt("expression","Expression","","e.g. sin(pi / 2) + sqrt(25)");
    form.insertBefore(group("Expression",[expr]),form.querySelector(".form-actions"));
    addMathKeypad(form,"Scientific Calculator");
    form.addEventListener("submit",async event=>{event.preventDefault();if(isBusy)return;isBusy=true;const submit=form.querySelector('[type="submit"]');submit.disabled=true;submit.textContent="Calculating…";try{const expression=val(form,"expression");if(!expression)throw new Error("Enter an expression to calculate.");const result=await api("/api/v1/calculate",{expression:transformDegreeTrig(expression)});renderResult(body,result,form);saveHistory({expression,result:result.result,displayedResult:formatNumber(result.result),angleMode,timestamp:new Date().toISOString()});}catch(error){body.replaceChildren();const p=document.createElement("p");p.className="result-error";p.textContent=error.message;body.append(p);}finally{isBusy=false;submit.disabled=false;submit.textContent="Calculate";}});
    output.append(historySection());
    const reference=formulaReferenceCard("Scientific Calculator");if(reference)workspace.append(reference);
    form.elements.expression.addEventListener("keydown",event=>{if(event.key==="Enter"){event.preventDefault();form.requestSubmit();}});
  }

  async function submitForm(form) {
    switch(activeTool){
      case "Equations": {
        const mode=val(form,"equation_mode");
        if(mode==="binomial")return api("/api/v1/binomials/expand",{expression:val(form,"expression")});
        if(mode==="system")return api("/api/v1/equations/system",{equations:val(form,"system_equations").split(/\n+/).map(line=>line.trim()).filter(Boolean)});
        const equation=val(form,"equation").replace(/[−–]/g,"-").trim();
        if(!equation.includes("="))throw new Error("Enter an equation with an equals sign, for example x^2 + y = 5.");
        if(/\by\b/i.test(equation)){const relation=equation.replace(/\bz\b/gi,"0");const graph=await api("/api/v1/graph/relation",{relation,x_min:-10,x_max:10,y_min:-10,y_max:10,grid_size:100});return {...graph,relation,graph_only:true,message:"This is a two-variable relation. Its curve is plotted below; any z terms are fixed at zero for this 2D view."};}
        return api("/api/v1/equations/solve",{equation, equation_type:mode});
      }
      case "Graphing Calculator": {
        const x_min=number(form,"x_min"),x_max=number(form,"x_max"),points=integer(form,"points");
        const y_min=number(form,"y_min"),y_max=number(form,"y_max");
        if(x_min>=x_max)throw new Error("Maximum x must be greater than minimum x.");
        if(y_min>=y_max)throw new Error("Maximum y must be greater than minimum y.");
        if(points<2||points>2000)throw new Error("Sample points must be between 2 and 2,000.");
        const expression=val(form,"expression").replace(/[−–]/g,"-").trim();
        if(!expression)throw new Error("Enter a function or equation to graph.");
        if(/\by\b/i.test(expression)||expression.includes("=")){
          return api("/api/v1/graph/relation",{relation:expression,x_min,x_max,y_min,y_max,grid_size:Math.max(40,Math.min(120,Math.round(Math.sqrt(points)*4)))});
        }
        return api("/api/v1/graph/sample",{expression,x_min,x_max,points});
      }
      case "Calculus": {const operation=val(form,"operation"),payload={operation,expression:val(form,"expression"),variable:val(form,"variable"),order:integer(form,"order"),direction:val(form,"direction"),point:val(form,"point")||"0"};if(operation==="definite_integral"){payload.lower=val(form,"lower");payload.upper=val(form,"upper");}if(operation==="integral"){delete payload.point;delete payload.direction;}return api("/api/v1/calculus",payload);}
      case "Matrix Calculator": {
        const operation=val(form,"operation"),payload={operation,steps:true};
        const two=["add","subtract","multiply","equals"];
        if(!["identity","zero"].includes(operation))payload.matrix=matrixValue(form,"matrix_a");
        if(two.includes(operation))payload.matrix_b=matrixValue(form,"matrix_b");
        if(operation==="scalar_multiply")payload.scalar=val(form,"scalar");
        if(operation==="power")payload.power=integer(form,"power");
        if(["identity","zero"].includes(operation))payload.size=integer(form,"size");
        if(["minor","cofactor"].includes(operation)){payload.row=integer(form,"row");payload.column=integer(form,"column");}
        if(["solve","cramer"].includes(operation))payload.vector=csvNumbers(form,"vector").map(String);
        if(operation==="inverse"&&val(form,"method"))payload.method=val(form,"method");
        return api("/api/v1/matrices/operations",payload);
      }
      case "Statistics": return api("/api/v1/statistics",{operation:val(form,"operation"),values:csvNumbers(form,"values")});
      case "Probability & Combinatorics": {const operation=val(form,"operation"),payload={operation};["favorable","total","event_a","event_b","intersection","n","r","p","k"].forEach(key=>{const raw=val(form,key);if(raw!=="")payload[key]=Number(raw);});return api("/api/v1/probability",payload);}
      case "Unit Converter": {const mode=val(form,"conversion_type");if(mode==="currency")return api("/api/v1/currency/convert",{amount:number(form,"amount"),from_currency:val(form,"from_currency").toUpperCase(),to_currency:val(form,"to_currency").toUpperCase()});if(mode==="base")return api("/api/v1/numbers/convert-base",{value:val(form,"base_value"),from_base:integer(form,"from_base"),to_base:integer(form,"to_base")});return api("/api/v1/units/convert",{value:number(form,"value"),from_unit:val(form,"from_unit"),to_unit:val(form,"to_unit")});}
      case "Finance & Loan EMI": {const op=val(form,"operation");if(op==="simple-interest")return api("/api/v1/finance/simple-interest",{principal:number(form,"principal"),annual_rate:number(form,"annual_rate"),years:number(form,"years")});if(op==="compound-interest")return api("/api/v1/finance/compound-interest",{principal:number(form,"principal"),annual_rate:number(form,"annual_rate"),years:number(form,"years"),compounding_per_year:integer(form,"compounding_per_year")});return api("/api/v1/finance/emi",{principal:number(form,"principal"),annual_rate:number(form,"annual_rate"),tenure_months:integer(form,"tenure_months")});}
      case "Discount & GST Calculator": {if(val(form,"operation")==="discount")return api("/api/v1/discount/calculate",{price:number(form,"price"),discount_percent:number(form,"discount_percent")});return api("/api/v1/gst/calculate",{amount:number(form,"price"),gst_rate:number(form,"gst_rate"),inclusive:val(form,"inclusive")==="true"});}
      case "BMI Calculator": {const age=integer(form,"age");if(age<15||age>120)throw new Error("This BMI calculator is intended for people aged 15 or older.");const unit=val(form,"height_unit");let height_m;if(unit==="imperial"){const feet=number(form,"height_feet"),inches=number(form,"height_inches");if(feet<0||inches<0||inches>=12)throw new Error("Enter a non-negative feet value and inches from 0 to less than 12.");height_m=(feet*12+inches)*0.0254;}else{const cm=number(form,"height_cm");if(cm<=0)throw new Error("Height must be greater than zero.");height_m=cm/100;}if(height_m<=0)throw new Error("Height must be greater than zero.");return api("/api/v1/health/bmi",{weight_kg:number(form,"weight_kg"),height_m});}
      case "Date Calculator": {const operation=val(form,"operation"),payload={operation,date:val(form,"date"),days:integer(form,"days")||0};if(operation==="difference")payload.other_date=val(form,"other_date");return api("/api/v1/dates/calculate",payload);}
      default: throw new Error("This tool is not configured yet.");
    }
  }

  function renderTool(title) {
    if(title==="Quadratic & Polynomial Solver" || title==="Binomial Expansion") title="Equations";
    activeTool=title;document.body.classList.toggle("studio-active",title==="Advanced Maths Studio");pageTitle.textContent=title;workspaceTitle.textContent=title;workspaceSubtitle.textContent=descriptions[title]||"";
    angleToggle.hidden=title!=="Scientific Calculator";
    navItems.forEach(item=>{const selected=item.dataset.tool===title;item.classList.toggle("is-active",selected);if(selected)item.setAttribute("aria-current","page");else item.removeAttribute("aria-current");});
    setDrawer(false);if(title==="Scientific Calculator"){scientificWorkspace();return;}
    if(title==="Advanced Maths Studio"){const frame=document.createElement("iframe");frame.className="advanced-studio-frame";frame.title="Advanced Maths Studio";frame.src="./studio.html";frame.loading="eager";frame.referrerPolicy="strict-origin-when-cross-origin";frame.style.cssText="display:block;width:100%;height:calc(100vh - 150px);min-height:1100px;border:0;border-radius:12px;background:#080d18";workspace.replaceChildren(frame);return;}
    let spec=[];
    switch(title){
      case "Equations":spec=[["Equation type",[sel("equation_mode","Choose a tool",[
        ["polynomial","General polynomial equation (any degree)"],
        ["linear","Single-variable linear equation"],
        ["quadratic","Single-variable quadratic equation"],
        ["multivariable_linear","Multivariable linear equation"],
        ["multivariable_quadratic","Multivariable quadratic equation"],
        ["system","System of equations"],
        ["binomial","Binomial theorem / expansion"]
      ])]],["Single equation",[txt("equation","Equation","","e.g. xy + yz = 3x^2yz","Use an equals sign. General polynomial mode accepts mixed terms and any degree in x, y, and z.")]],["System of equations",[area("system_equations","Equations (one per line)","x + y = 5\ny - x = 1","Enter each equation on a separate line.")]],["Binomial expansion",[txt("expression","Binomial expression","","e.g. (x + 2)^3")]]];break;
      case "Graphing Calculator":spec=[["Function or equation",[txt("expression","Function or equation","","e.g. sin(x), y = x^2, or y^2 = 18x"),num("x_min","Minimum x","-10"),num("x_max","Maximum x","10"),num("y_min","Minimum y","-10"),num("y_max","Maximum y","10"),num("points","Sample points","401","Functions use 2–2,000 samples; implicit equations use a contour grid.")]]];break;
      case "Calculus":spec=[["Calculus operation",[sel("operation","Operation",selectOptions.calculusOperation),sel("variable","Variable",options(["x","y","z","t"])),num("order","Derivative order","1"),txt("expression","Expression","","e.g. x^3 + sin(x)"),txt("lower","Lower bound","0"),txt("upper","Upper bound","1"),txt("point","Limit point","0"),sel("direction","Limit direction",options(["both","plus","minus"]))]]];break;
      case "Matrix Calculator":spec=[["Matrix operation",[sel("operation","Matrix operation",selectOptions.matrixOperation),area("matrix_a","Matrix A","1, 2\n3, 4","Rows separated by new lines; values separated by commas."),area("matrix_b","Matrix B","5, 6\n7, 8","Required for add, subtract, multiply, and compare."),txt("scalar","Scalar","2"),num("power","Power","2"),num("size","Size for identity/zero","3"),num("row","Row (1-based)","1"),num("column","Column (1-based)","1"),area("vector","Vector b","5, 11","For solving Ax = b; values separated by commas."),sel("method","Inverse method",[["","Default"],["adjoint","Adjoint"],["gauss_jordan","Gauss–Jordan"]]),sel("steps","Step-by-step working",[["true","On"],["false","Off"]])]]];break;
      case "Statistics":spec=[["Dataset",[sel("operation","Statistic",selectOptions.statsOperation),area("values","Values","12, 15, 18, 18, 21","Separate observations with commas, spaces, or new lines.")]]];break;
      case "Probability & Combinatorics":spec=[["Probability or counting inputs",[sel("operation","Operation",selectOptions.probabilityOperation),num("favorable","Favourable outcomes","1"),num("total","Total outcomes","6"),num("event_a","P(A)","0.5"),num("event_b","P(B)","0.4"),num("intersection","P(A ∩ B)","0.2"),num("n","n","5"),num("r","r","2"),num("p","Success probability p","0.5"),num("k","Successes k","2")]]];break;
      case "Unit Converter":{const dims=capabilities?.unit_dimensions||[],fallback=[{id:"length",units:["m","cm","km","mm","ft","in"]},{id:"mass",units:["kg","g","mg","lb","oz"]},{id:"temperature",units:["celsius","fahrenheit","kelvin"]},{id:"time",units:["s","min","h","day"]},{id:"volume",units:["L","mL"]}];const categories=dims.length?dims:fallback;const categoryOptions=categories.map(d=>[d.id,d.id.replaceAll("_"," ").replace(/\b\w/g,c=>c.toUpperCase())]);const initial=categories[0];const unitOptions=initial.units.map(unit=>[unit,String(unit).replaceAll("_"," ").replace(/\b\w/g,c=>c.toUpperCase())]);spec=[["Conversion type",[sel("conversion_type","What do you want to convert?",[["units","Physical units"],["currency","Currency"],["base","Number base"]])]],["Unit category",[sel("dimension","Unit category",categoryOptions)]],["Unit conversion",[num("value","Value","1"),sel("from_unit","From unit",unitOptions),sel("to_unit","To unit",unitOptions)]],["Currency conversion",[num("amount","Amount","100"),sel("from_currency","From currency",options(["INR","USD","EUR","GBP","JPY","CAD","AUD","CNY","SGD","AED"])),sel("to_currency","To currency",options(["USD","INR","EUR","GBP","JPY","CAD","AUD","CNY","SGD","AED"]))]],["Number base conversion",[txt("base_value","Integer value","255","e.g. 255 or FF"),num("from_base","From base","10"),num("to_base","To base","16")]]];break;}
      case "Finance & Loan EMI":spec=[["Finance calculation",[sel("operation","Calculation",selectOptions.financeOperation),num("principal","Principal / loan amount","100000"),num("annual_rate","Annual interest rate (%)","8.5"),num("years","Term (years)","5"),num("compounding_per_year","Compounds per year","12"),num("tenure_months","Loan tenure (months)","60")]]];break;
      case "Discount & GST Calculator":spec=[["Discount or GST",[sel("operation","Calculation",[["discount","Discount"],["gst","GST"]]),num("price","Price / amount","1000"),num("discount_percent","Discount (%)","10"),num("gst_rate","GST rate (%)","18"),sel("inclusive","GST amount includes tax?",[["false","No — add GST"],["true","Yes — extract GST"]])]]];break;
      case "BMI Calculator":spec=[["About the person",[num("age","Age (years)","18"),sel("sex_reference","Sex for reference",[["female","Female"],["male","Male"]])]],["Body measurements",[num("weight_kg","Weight (kg)","70"),sel("height_unit","Height unit",[["metric","Centimetres"],["imperial","Feet and inches"]]),num("height_cm","Height (cm)","175"),num("height_feet","Feet","5"),num("height_inches","Additional inches","9")]]];break;
      case "Date Calculator":spec=[["Date calculation",[sel("operation","Operation",selectOptions.dateOperation),field("date","Date",{type:"text",value:new Date().toISOString().slice(0,10),help:"Use YYYY-MM-DD."}),num("days","Number of days","7"),field("other_date","Second date",{type:"text",value:new Date().toISOString().slice(0,10),help:"Only used for date difference; YYYY-MM-DD."})]]];break;
    }
    const {form}=createPanel(title,descriptions[title]);addFields(form,spec);
    addMathKeypad(form,title);
    if(title==="Equations"){
      const mode=form.elements.equation_mode;
      const updateEquationMode=()=>{
        const selected=mode.value,system=selected==="system",binomial=selected==="binomial";
        form.elements.equation.closest(".field").hidden=system||binomial;
        form.elements.system_equations.closest(".field").hidden=!system;
        form.elements.expression.closest(".field").hidden=!binomial;
        form.querySelectorAll(".form-section").forEach(section=>{
          const fields=[...section.querySelectorAll(".field")];
          section.hidden=fields.length>0&&fields.every(item=>item.hidden);
        });
      };
      mode.addEventListener("change",updateEquationMode);updateEquationMode();
    }
    if(title==="Graphing Calculator"){
      const expression=form.elements.expression;
      expression.setAttribute("aria-describedby","graph-expression-help");
      const help=document.createElement("small");help.className="field-help";help.id="graph-expression-help";help.textContent="Enter y = f(x) or an implicit equation such as y^2 = 18x, x^2 + y^2 = 25, or x = y. The graphing engine plots both branches and conic sections."
      expression.closest(".field").append(help);
    }
    if(title==="Unit Converter"){
      const conversionType=form.elements.conversion_type;
      const updateConversionType=()=>{const type=conversionType.value;const show=(name,yes)=>{const el=form.elements[name];if(el)el.closest(".field").hidden=!yes;};show("dimension",type==="units");["value","from_unit","to_unit"].forEach(n=>show(n,type==="units"));["amount","from_currency","to_currency"].forEach(n=>show(n,type==="currency"));["base_value","from_base","to_base"].forEach(n=>show(n,type==="base"));};
      conversionType.addEventListener("change",updateConversionType);updateConversionType();
      const category=form.elements.dimension,from=form.elements.from_unit,to=form.elements.to_unit;
      const updateUnits=()=>{
        const dims=capabilities?.unit_dimensions||[{id:"length",units:["m","cm","km","mm","ft","in"]},{id:"mass",units:["kg","g","mg","lb","oz"]},{id:"temperature",units:["celsius","fahrenheit","kelvin"]},{id:"time",units:["s","min","h","day"]},{id:"volume",units:["L","mL"]}];
        const selected=dims.find(d=>d.id===category.value)||dims[0];if(!selected)return;
        const previousFrom=from.value,previousTo=to.value;
        const unitOptions=selected.units.map(unit=>[unit,String(unit).replaceAll("_"," ").replace(/\\b\\w/g,c=>c.toUpperCase())]);
        [from,to].forEach(select=>{select.replaceChildren();unitOptions.forEach(([value,label])=>{const option=document.createElement("option");option.value=value;option.textContent=label;select.append(option);});});
        from.value=selected.units.includes(previousFrom)?previousFrom:selected.units[0];
        to.value=selected.units.includes(previousTo)?previousTo:(selected.units[1]||selected.units[0]);
      };
      category.addEventListener("change",updateUnits);updateUnits();
    }
    if(title==="Matrix Calculator"){
      const op=form.elements.operation;
      const update=()=>{const v=op.value,hide=(name,yes)=>{form.elements[name].closest(".field").hidden=!yes;};
        hide("matrix_a",!["identity","zero"].includes(v));hide("matrix_b",["add","subtract","multiply","equals"].includes(v));hide("scalar",v==="scalar_multiply");hide("power",v==="power");hide("size",["identity","zero"].includes(v));hide("row",["minor","cofactor"].includes(v));hide("column",["minor","cofactor"].includes(v));hide("vector",["solve","cramer"].includes(v));hide("method",v==="inverse");hide("steps",true);};
      op.addEventListener("change",update);update();
    }
    if(title==="Calculus"){
      const op=form.elements.operation;const update=()=>{const v=op.value;form.elements.lower.closest(".field").hidden=v!=="definite_integral";form.elements.upper.closest(".field").hidden=v!=="definite_integral";form.elements.point.closest(".field").hidden=v!=="limit";form.elements.direction.closest(".field").hidden=v!=="limit";form.elements.order.closest(".field").hidden=v!=="derivative";};op.addEventListener("change",update);update();
    }
    if(title==="Probability & Combinatorics"){
      const op=form.elements.operation;const update=()=>{const v=op.value,show=(name,yes)=>{form.elements[name].closest(".field").hidden=!yes;};show("favorable",v==="simple");show("total",v==="simple");show("event_a",["conditional","union"].includes(v));show("event_b",["conditional","union"].includes(v));show("intersection",["conditional","union"].includes(v));show("n",["permutation","combination","binomial"].includes(v));show("r",["permutation","combination"].includes(v));show("p",v==="binomial");show("k",v==="binomial");};op.addEventListener("change",update);update();
    }
    if(title==="Finance & Loan EMI"){
      const op=form.elements.operation;const update=()=>{form.elements.years.closest(".field").hidden=op.value==="emi";form.elements.compounding_per_year.closest(".field").hidden=op.value!=="compound-interest";form.elements.tenure_months.closest(".field").hidden=op.value!=="emi";};op.addEventListener("change",update);update();
    }
    if(title==="Discount & GST Calculator"){
      const op=form.elements.operation;const update=()=>{const discount=op.value==="discount";form.elements.price.closest(".field").querySelector(".field-label").textContent=discount?"Price":"Amount";form.elements.discount_percent.closest(".field").hidden=!discount;form.elements.gst_rate.closest(".field").hidden=discount;form.elements.inclusive.closest(".field").hidden=discount;};op.addEventListener("change",update);update();
    }
    if(title==="BMI Calculator"){const age=form.elements.age;age.min="15";age.max="120";age.step="1";const unit=form.elements.height_unit,update=()=>{const imperial=unit.value==="imperial";form.elements.height_cm.closest(".field").hidden=imperial;form.elements.height_feet.closest(".field").hidden=!imperial;form.elements.height_inches.closest(".field").hidden=!imperial;};unit.addEventListener("change",update);update();}
    if(title==="Date Calculator"){
      const op=form.elements.operation;const update=()=>{form.elements.days.closest(".field").hidden=op.value==="difference";form.elements.other_date.closest(".field").hidden=op.value!=="difference";};op.addEventListener("change",update);update();
    }
    const reference=formulaReferenceCard(title);if(reference)workspace.append(reference);
  }

  const previewExamples = {
    scientific: {label:"SCIENTIFIC CALCULATION", expression:"sin(30°)", answer:"0.5", detail:"Trigonometric ratio"},
    equations: {label:"SOLVING AN EQUATION", expression:"2x + 3 = 11", answer:"x = 4", detail:"Subtract 3, then divide by 2"},
    calculus: {label:"DIFFERENTIATION", expression:"d/dx (x³) at x = 2", answer:"12", detail:"Derivative: 3x²"},
    matrices: {label:"MATRIX DETERMINANT", expression:"A = [[1, 2], [3, 4]]", answer:"−2", detail:"det(A) = (1 × 4) − (2 × 3)"}
  };
  const previewButtons = document.querySelectorAll("[data-preview]");
  previewButtons.forEach(button => button.addEventListener("click", () => {
    const example = previewExamples[button.dataset.preview];
    if (!example) return;
    const label = $("#preview-mode-label");
    const expression = $("#preview-equation");
    const answer = $("#preview-answer");
    const detail = $("#preview-detail");
    if (label) label.textContent = example.label;
    if (expression) expression.textContent = example.expression;
    if (answer) answer.textContent = example.answer;
    if (detail) detail.textContent = example.detail;
    previewButtons.forEach(item => {
      const selected = item === button;
      item.classList.toggle("is-selected", selected);
      item.setAttribute("aria-pressed", String(selected));
    });
  }));

  const feedbackDialog = $("#feedback-dialog");
  const feedbackForm = $("#feedback-form");
  const feedbackStatus = $("#feedback-status");
  const feedbackFrame = $("#feedback-submit-frame");
  const feedbackOpeners = $$("[data-open-feedback]");
  const feedbackClosers = $$("[data-close-feedback]");
  let feedbackPending = false;
  let feedbackTimeout = null;
  feedbackOpeners.forEach(button => button.addEventListener("click", () => {
    if (feedbackDialog && typeof feedbackDialog.showModal === "function") feedbackDialog.showModal();
  }));
  feedbackClosers.forEach(button => button.addEventListener("click", () => feedbackDialog?.close()));
  if (feedbackDialog) feedbackDialog.addEventListener("click", event => {
    if (event.target === feedbackDialog) feedbackDialog.close();
  });
  if (feedbackFrame) feedbackFrame.addEventListener("load", () => {
    if (!feedbackPending) return;
    feedbackPending = false;
    window.clearTimeout(feedbackTimeout);
    feedbackForm.reset();
    const submit = feedbackForm.querySelector('[type="submit"]');
    submit.disabled = false;
    submit.innerHTML = 'Send feedback <span aria-hidden="true">→</span>';
    feedbackStatus.textContent = "Your feedback form was submitted. If this is your first submission, the project owner may need to activate FormSubmit by email before messages are delivered.";
    feedbackStatus.className = "feedback-status is-success";
  });
  if (feedbackForm) feedbackForm.addEventListener("submit", event => {
    if (!feedbackForm.reportValidity()) {
      event.preventDefault();
      return;
    }
    const honey = feedbackForm.querySelector('[name="_honey"]');
    if (honey && honey.value.trim()) {
      event.preventDefault();
      return;
    }
    const submit = feedbackForm.querySelector('[type="submit"]');
    submit.disabled = true;
    submit.textContent = "Sending…";
    feedbackStatus.textContent = "Sending your feedback…";
    feedbackStatus.className = "feedback-status";
    feedbackPending = true;
    window.clearTimeout(feedbackTimeout);
    feedbackTimeout = window.setTimeout(() => {
      if (!feedbackPending) return;
      feedbackPending = false;
      submit.disabled = false;
      submit.innerHTML = 'Send feedback <span aria-hidden="true">→</span>';
      feedbackStatus.textContent = "The feedback service did not respond. Please check your connection and try again.";
      feedbackStatus.className = "feedback-status is-error";
    }, 20000);
  });

  const studioHomeLink = $("#open-studio-from-home");
  if (studioHomeLink) studioHomeLink.addEventListener("click", event => { event.preventDefault(); document.body.classList.add("calculator-open"); history.replaceState(null, "", "#calculator"); window.scrollTo({top:0,behavior:"smooth"}); renderTool("Advanced Maths Studio"); });
  const startCalculating = $("#start-calculating");
  if (startCalculating) startCalculating.addEventListener("click", event => {
    event.preventDefault();
    document.body.classList.add("calculator-open");
    history.replaceState(null, "", "#calculator");
    window.scrollTo({top:0,behavior:"smooth"});
    renderTool("Scientific Calculator");
  });
  if (window.location.hash === "#calculator") document.body.classList.add("calculator-open");
  const homeYear = $("#home-year");
  if (homeYear) homeYear.textContent = String(new Date().getFullYear());
  const sidebarBrand = $(".sidebar .brand");
  if (sidebarBrand) sidebarBrand.addEventListener("click", event => {
    event.preventDefault();
    document.body.classList.remove("calculator-open");
    history.replaceState(null, "", window.location.pathname + window.location.search);
    window.scrollTo({top:0,behavior:"smooth"});
    setDrawer(false);
  });
  navItems.forEach(item=>item.addEventListener("click",()=>renderTool(item.dataset.tool)));
  renderTool(activeTool);checkApi();
})();