(() => {
  "use strict";
  const API_BASE_URL = (window.CALCULATOR_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
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
    "Quadratic & Polynomial Solver": "Solve polynomial equations and inspect their mathematical roots.",
    "Binomial Expansion": "Expand binomial expressions using the symbolic calculation engine.",
    "Graphing Calculator": "Sample and plot a function over a range of x-values.",
    "Calculus": "Calculate derivatives, integrals, definite integrals, and limits.",
    "Matrix Calculator": "Run matrix arithmetic and linear algebra operations.",
    "Statistics": "Summarize a dataset with descriptive statistical measures.",
    "Probability & Combinatorics": "Calculate event probabilities, permutations, combinations, and binomial probabilities.",
    "Unit Converter": "Convert values between supported measurement units.",
    "Currency Converter": "Convert currencies using the backend's available exchange-rate provider.",
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
    "Quadratic & Polynomial Solver": {kind:"equation"},
    "Binomial Expansion": {kind:"binomial"},
    "Graphing Calculator": {kind:"graph"},
    "Calculus": {kind:"calculus"},
    "Matrix Calculator": {kind:"matrix"},
    "Statistics": {kind:"statistics"},
    "Probability & Combinatorics": {kind:"probability"},
    "Unit Converter": {kind:"units"},
    "Currency Converter": {kind:"currency"},
    "Finance & Loan EMI": {kind:"finance"},
    "Discount & GST Calculator": {kind:"discount"},
    "Number Base Converter": {kind:"base"},
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
  async function api(path, body) {
    const options = body === undefined ? {method:"GET"} : {method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify(body)};
    let response;
    try { response = await fetch(API_BASE_URL + path, options); }
    catch { throw new Error("Could not reach the calculator API. Check that the backend is running and the API URL/CORS settings are correct."); }
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
    const grid=document.createElement("div"); grid.className="workspace-grid tool-grid";
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
      try { const result=await submitForm(form); renderResult(body,result); }
      catch(error) { body.replaceChildren();const message=document.createElement("p");message.className="result-error";message.textContent=error.message;body.append(message); }
      finally { submit.disabled=false;submit.textContent=original;isBusy=false; }
    });
    const actions=document.createElement("div");actions.className="form-actions";actions.append(button("Calculate"));
    form.append(actions);panel.append(form);grid.append(panel,output);workspace.append(grid);
    return {form,body,output};
  }
  function addFields(form, sections) { sections.forEach(([title,fields])=>form.insertBefore(group(title,fields),form.querySelector(".form-actions"))); }
  function val(form,name) { const el=form.elements.namedItem(name); return el ? el.value.trim() : ""; }
  function number(form,name) { const raw=val(form,name); const value=Number(raw); if(raw===""||!Number.isFinite(value))throw new Error("Enter a valid finite number for "+name.replaceAll("_"," ")+"."); return value; }
  function integer(form,name) { const value=number(form,name); if(!Number.isInteger(value))throw new Error(name.replaceAll("_"," ")+" must be a whole number.");return value; }
  function csvNumbers(form,name) { const values=val(form,name).split(/[\s,;]+/).filter(Boolean).map(Number);if(!values.length||values.some(v=>!Number.isFinite(v)))throw new Error("Enter one or more valid numbers separated by commas or spaces.");return values; }
  function matrixValue(form,name) {
    const raw=val(form,name);if(!raw)throw new Error("Enter matrix "+name.replace("matrix","").trim()+".");
    const rows=raw.split(/\n|;/).map(row=>row.trim()).filter(Boolean).map(row=>row.split(/[,\s]+/).filter(Boolean).map(token=>{
      if(!/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:\/\d+)?$/.test(token))throw new Error("Matrix cells must be numbers or simple fractions such as 3/4.");return token;
    }));
    if(!rows.length||rows.some(row=>row.length!==rows[0].length))throw new Error("Each matrix must be rectangular with the same number of values per row.");
    if(rows.length>8||rows[0].length>8)throw new Error("Matrix dimensions are limited to 8 × 8 by the API.");
    return rows;
  }
  function renderResult(container,result) {
    container.replaceChildren();
    if(result&&typeof result==="object"&&Array.isArray(result.points)){const points=result.points.filter(point=>Number.isFinite(point.x)&&Number.isFinite(point.y));if(points.length)container.append(drawGraph(result.points));}
    const pre=document.createElement("pre");pre.className="result-json";pre.textContent=typeof result==="string"?result:JSON.stringify(result,null,2);container.append(pre);
    const copy=button("Copy result","secondary-button","button");copy.addEventListener("click",async()=>{const text=pre.textContent;try{await navigator.clipboard.writeText(text);copy.textContent="Copied";}catch{const ta=document.createElement("textarea");ta.value=text;document.body.append(ta);ta.select();const ok=document.execCommand("copy");ta.remove();copy.textContent=ok?"Copied":"Copy unavailable";}});container.append(copy);
  }
  function drawGraph(points) {
    const figure=document.createElement("figure");figure.className="graph-figure";
    const width=640,height=320,pad=30,valid=points.filter(p=>Number.isFinite(p.x)&&Number.isFinite(p.y));
    if(valid.length<2)return figure;
    let xmin=Math.min(...valid.map(p=>p.x)),xmax=Math.max(...valid.map(p=>p.x)),ymin=Math.min(...valid.map(p=>p.y)),ymax=Math.max(...valid.map(p=>p.y));
    if(xmin===xmax){xmin-=1;xmax+=1;}if(ymin===ymax){ymin-=1;ymax+=1;}
    const px=x=>pad+(x-xmin)/(xmax-xmin)*(width-pad*2),py=y=>height-pad-(y-ymin)/(ymax-ymin)*(height-pad*2),ns="http://www.w3.org/2000/svg";
    const svg=document.createElementNS(ns,"svg");svg.setAttribute("viewBox","0 0 "+width+" "+height);svg.setAttribute("role","img");svg.setAttribute("aria-label","Sampled function graph");
    function line(x1,y1,x2,y2,cls){const el=document.createElementNS(ns,"line");Object.entries({x1,y1,x2,y2}).forEach(([k,v])=>el.setAttribute(k,v));el.setAttribute("class",cls);svg.append(el);}
    for(let i=0;i<=4;i++){const x=pad+i*(width-pad*2)/4;line(x,pad,x,height-pad,"graph-grid");const y=pad+i*(height-pad*2)/4;line(pad,y,width-pad,y,"graph-grid");}
    if(xmin<=0&&xmax>=0)line(px(0),pad,px(0),height-pad,"graph-axis");if(ymin<=0&&ymax>=0)line(pad,py(0),width-pad,py(0),"graph-axis");
    let d="",active=false;points.forEach(p=>{if(!Number.isFinite(p.x)||!Number.isFinite(p.y)){active=false;return;}d+=(active?"L":"M")+px(p.x).toFixed(2)+","+py(p.y).toFixed(2)+" ";active=true;});
    const path=document.createElementNS(ns,"path");path.setAttribute("d",d);path.setAttribute("class","graph-curve");svg.append(path);figure.append(svg);
    const caption=document.createElement("figcaption");caption.textContent="x: "+xmin.toPrecision(4)+" to "+xmax.toPrecision(4)+" · y: "+ymin.toPrecision(4)+" to "+ymax.toPrecision(4);figure.append(caption);return figure;
  }
  function transformDegreeTrig(expression) {
    if(angleMode!=="DEG")return expression;
    const names=new Set(["sin","cos","tan"]);let out="",i=0;
    while(i<expression.length){const match=expression.slice(i).match(/^([A-Za-z_][A-Za-z_0-9]*)\s*\(/);if(!match){out+=expression[i++];continue;}
      const name=match[1],open=i+match[0].lastIndexOf("(");let depth=1,j=open+1;
      while(j<expression.length&&depth>0){if(expression[j]==="(")depth++;else if(expression[j]===")")depth--;j++;}
      if(depth!==0){out+=expression.slice(i);break;}
      const inner=transformDegreeTrig(expression.slice(open+1,j-1));out+=names.has(name.toLowerCase())?name+"(radians("+inner+"))":name+"("+inner+")";i=j;
    }return out;
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
  function scientificWorkspace(){
    angleToggle.hidden=false;
    const {form,body,output}=createPanel("Scientific Calculator","Type an expression or use the keypad. Evaluation is handled by the Python engine.");
    const expr=txt("expression","Expression","","e.g. sin(pi / 2) + sqrt(25)");
    form.insertBefore(group("Expression",[expr]),form.querySelector(".form-actions"));
    const keypad=document.createElement("div");keypad.className="keypad functional-keypad";
    const keys=[["sin(","function"],["cos(","function"],["tan(","function"],["ln(","function"],["log(","function"],["sqrt(","function"],["^2","function"],["^","function"],["(","function"],[")","function"],["7",""],["8",""],["9",""],["/","operator"],["⌫","operator"],["4",""],["5",""],["6",""],["*","operator"],["AC","operator"],["1",""],["2",""],["3",""],["-","operator"],["+","operator"],["pi","function"],["0",""],[".",""],["%","function"],["=","equals"]];
    keys.forEach(([text,kind])=>{const b=button(text,"key "+(kind==="function"?"key-function":kind==="operator"?"key-operator":kind==="equals"?"key-equals":""),"button");b.addEventListener("click",()=>{const input=form.elements.expression;if(text==="=")form.requestSubmit();else if(text==="AC"){input.value="";input.focus();}else if(text==="⌫"){const start=input.selectionStart??input.value.length,end=input.selectionEnd??start;input.setRangeText("",start===end?Math.max(0,start-1):start,end,"end");input.focus();}else{const start=input.selectionStart??input.value.length,end=input.selectionEnd??start;input.setRangeText(text,start,end,"end");input.focus();}});keypad.append(b);});
    form.insertBefore(keypad,form.querySelector(".form-actions"));
    form.addEventListener("submit",async event=>{event.preventDefault();if(isBusy)return;isBusy=true;const submit=form.querySelector('[type="submit"]');submit.disabled=true;submit.textContent="Calculating…";try{const expression=val(form,"expression");if(!expression)throw new Error("Enter an expression to calculate.");const result=await api("/api/v1/calculate",{expression:transformDegreeTrig(expression)});renderResult(body,result);saveHistory({expression,result:result.result,displayedResult:formatNumber(result.result),angleMode,timestamp:new Date().toISOString()});}catch(error){body.replaceChildren();const p=document.createElement("p");p.className="result-error";p.textContent=error.message;body.append(p);}finally{isBusy=false;submit.disabled=false;submit.textContent="Calculate";}});
    output.append(historySection());
    form.elements.expression.addEventListener("keydown",event=>{if(event.key==="Enter"){event.preventDefault();form.requestSubmit();}});
  }

  async function submitForm(form) {
    switch(activeTool){
      case "Quadratic & Polynomial Solver": return api("/api/v1/equations/solve",{equation:val(form,"equation")});
      case "Binomial Expansion": return api("/api/v1/binomials/expand",{expression:val(form,"expression")});
      case "Graphing Calculator": {const x_min=number(form,"x_min"),x_max=number(form,"x_max"),points=integer(form,"points");if(x_min>=x_max)throw new Error("Maximum x must be greater than minimum x.");if(points<2||points>2000)throw new Error("Sample points must be between 2 and 2,000.");return api("/api/v1/graph/sample",{expression:val(form,"expression"),x_min,x_max,points});}
      case "Calculus": {const operation=val(form,"operation"),payload={operation,expression:val(form,"expression"),variable:val(form,"variable"),order:integer(form,"order"),direction:val(form,"direction"),point:val(form,"point")||"0"};if(operation==="definite_integral"){payload.lower=val(form,"lower");payload.upper=val(form,"upper");}if(operation==="integral"){delete payload.point;delete payload.direction;}return api("/api/v1/calculus",payload);}
      case "Matrix Calculator": {
        const operation=val(form,"operation"),payload={operation,steps:val(form,"steps")==="true"};
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
      case "Unit Converter": return api("/api/v1/units/convert",{value:number(form,"value"),from_unit:val(form,"from_unit"),to_unit:val(form,"to_unit")});
      case "Currency Converter": return api("/api/v1/currency/convert",{amount:number(form,"amount"),from_currency:val(form,"from_currency").toUpperCase(),to_currency:val(form,"to_currency").toUpperCase()});
      case "Finance & Loan EMI": {const op=val(form,"operation");if(op==="simple-interest")return api("/api/v1/finance/simple-interest",{principal:number(form,"principal"),annual_rate:number(form,"annual_rate"),years:number(form,"years")});if(op==="compound-interest")return api("/api/v1/finance/compound-interest",{principal:number(form,"principal"),annual_rate:number(form,"annual_rate"),years:number(form,"years"),compounding_per_year:integer(form,"compounding_per_year")});return api("/api/v1/finance/emi",{principal:number(form,"principal"),annual_rate:number(form,"annual_rate"),tenure_months:integer(form,"tenure_months")});}
      case "Discount & GST Calculator": {if(val(form,"operation")==="discount")return api("/api/v1/discount/calculate",{price:number(form,"price"),discount_percent:number(form,"discount_percent")});return api("/api/v1/gst/calculate",{amount:number(form,"price"),gst_rate:number(form,"gst_rate"),inclusive:val(form,"inclusive")==="true"});}
      case "Number Base Converter": return api("/api/v1/numbers/convert-base",{value:val(form,"value"),from_base:integer(form,"from_base"),to_base:integer(form,"to_base")});
      case "BMI Calculator": return api("/api/v1/health/bmi",{weight_kg:number(form,"weight_kg"),height_m:number(form,"height_m")});
      case "Date Calculator": {const operation=val(form,"operation"),payload={operation,date:val(form,"date"),days:integer(form,"days")||0};if(operation==="difference")payload.other_date=val(form,"other_date");return api("/api/v1/dates/calculate",payload);}
      default: throw new Error("This tool is not configured yet.");
    }
  }

  function renderTool(title) {
    activeTool=title;pageTitle.textContent=title;workspaceTitle.textContent=title;workspaceSubtitle.textContent=descriptions[title]||"";
    angleToggle.hidden=title!=="Scientific Calculator";
    navItems.forEach(item=>{const selected=item.dataset.tool===title;item.classList.toggle("is-active",selected);if(selected)item.setAttribute("aria-current","page");else item.removeAttribute("aria-current");});
    setDrawer(false);if(title==="Scientific Calculator"){scientificWorkspace();return;}
    let spec=[];
    switch(title){
      case "Quadratic & Polynomial Solver":spec=[["Equation",[txt("equation","Equation in x","","e.g. x^2 - 5*x + 6 = 0","Use = 0 for a polynomial equation.")]]];break;
      case "Binomial Expansion":spec=[["Expression",[txt("expression","Binomial expression","","e.g. (x + 2)^3")]]];break;
      case "Graphing Calculator":spec=[["Function",[txt("expression","Function of x","","e.g. sin(x) or x^2 - 4"),num("x_min","Minimum x","-10"),num("x_max","Maximum x","10"),num("points","Sample points","201","Choose 2–2,000 points.")]]];break;
      case "Calculus":spec=[["Calculus operation",[sel("operation","Operation",selectOptions.calculusOperation),sel("variable","Variable",options(["x","y","z","t"])),num("order","Derivative order","1"),txt("expression","Expression","","e.g. x^3 + sin(x)"),txt("lower","Lower bound","0"),txt("upper","Upper bound","1"),txt("point","Limit point","0"),sel("direction","Limit direction",options(["both","plus","minus"]))]]];break;
      case "Matrix Calculator":spec=[["Matrix operation",[sel("operation","Matrix operation",selectOptions.matrixOperation),area("matrix_a","Matrix A","1, 2\n3, 4","Rows separated by new lines; values separated by commas."),area("matrix_b","Matrix B","5, 6\n7, 8","Required for add, subtract, multiply, and compare."),txt("scalar","Scalar","2"),num("power","Power","2"),num("size","Size for identity/zero","3"),num("row","Row (1-based)","1"),num("column","Column (1-based)","1"),area("vector","Vector b","5, 11","For solving Ax = b; values separated by commas."),sel("method","Inverse method",[["","Default"],["adjoint","Adjoint"],["gauss_jordan","Gauss–Jordan"]]),sel("steps","Step-by-step working",[["false","Off"],["true","On"]])]]];break;
      case "Statistics":spec=[["Dataset",[sel("operation","Statistic",selectOptions.statsOperation),area("values","Values","12, 15, 18, 18, 21","Separate observations with commas, spaces, or new lines.")]]];break;
      case "Probability & Combinatorics":spec=[["Probability or counting inputs",[sel("operation","Operation",selectOptions.probabilityOperation),num("favorable","Favourable outcomes","1"),num("total","Total outcomes","6"),num("event_a","P(A)","0.5"),num("event_b","P(B)","0.4"),num("intersection","P(A ∩ B)","0.2"),num("n","n","5"),num("r","r","2"),num("p","Success probability p","0.5"),num("k","Successes k","2")]]];break;
      case "Unit Converter":{const dims=capabilities?.unit_dimensions||[],unitList=[...new Set(dims.flatMap(d=>d.units))].sort(),unitOpts=options(unitList.length?unitList:["m","cm","km","mm","ft","in","kg","g","lb","s","min","h","L","mL"]);spec=[["Conversion",[num("value","Value","1"),sel("from_unit","From unit",unitOpts),sel("to_unit","To unit",unitOpts)]]];break;}
      case "Currency Converter":spec=[["Currency amount",[num("amount","Amount","100"),sel("from_currency","From currency",options(["INR","USD","EUR","GBP","JPY","CAD","AUD","CNY","SGD","AED"])),sel("to_currency","To currency",options(["USD","INR","EUR","GBP","JPY","CAD","AUD","CNY","SGD","AED"]))]]];break;
      case "Finance & Loan EMI":spec=[["Finance calculation",[sel("operation","Calculation",selectOptions.financeOperation),num("principal","Principal / loan amount","100000"),num("annual_rate","Annual interest rate (%)","8.5"),num("years","Term (years)","5"),num("compounding_per_year","Compounds per year","12"),num("tenure_months","Loan tenure (months)","60")]]];break;
      case "Discount & GST Calculator":spec=[["Discount or GST",[sel("operation","Calculation",[["discount","Discount"],["gst","GST"]]),num("price","Price / amount","1000"),num("discount_percent","Discount (%)","10"),num("gst_rate","GST rate (%)","18"),sel("inclusive","GST amount includes tax?",[["false","No — add GST"],["true","Yes — extract GST"]])]]];break;
      case "Number Base Converter":spec=[["Number conversion",[txt("value","Integer value","255","e.g. 255 or FF"),num("from_base","From base","10"),num("to_base","To base","16")]]];break;
      case "BMI Calculator":spec=[["Body measurements",[num("weight_kg","Weight (kg)","70"),num("height_m","Height (metres)","1.75")]]];break;
      case "Date Calculator":spec=[["Date calculation",[sel("operation","Operation",selectOptions.dateOperation),field("date","Date",{type:"text",value:new Date().toISOString().slice(0,10),help:"Use YYYY-MM-DD."}),num("days","Number of days","7"),field("other_date","Second date",{type:"text",value:new Date().toISOString().slice(0,10),help:"Only used for date difference; YYYY-MM-DD."})]]];break;
    }
    const {form}=createPanel(title,descriptions[title]);addFields(form,spec);
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
    if(title==="Date Calculator"){
      const op=form.elements.operation;const update=()=>{form.elements.days.closest(".field").hidden=op.value==="difference";form.elements.other_date.closest(".field").hidden=op.value!=="difference";};op.addEventListener("change",update);update();
    }
  }
  navItems.forEach(item=>item.addEventListener("click",()=>renderTool(item.dataset.tool)));
  renderTool(activeTool);checkApi();
})();