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
    "Graphing Calculator": "Sample and plot a function over a range of x-values.",
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
  async function api(path, body) {
    if (!API_BASE_URL) throw new Error("The calculator API URL is missing. Reload the site after the latest Render deployment; if the problem continues, check the frontend API_BASE_URL setting.");
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
      try {
        const result=await submitForm(form);
        renderResult(body,result);
        const inputs=[...form.querySelectorAll("input,select,textarea")].filter(el=>el.name&&el.value&&!el.closest(".field")?.hidden);
        const expression=activeTool+" · "+inputs.map(el=>el.name+"="+el.value).join(", ");
        const displayedResult=typeof result==="object"?(result.result!==undefined?String(result.result):result.message||result.status||JSON.stringify(result)):String(result);
        saveHistory({expression,displayedResult,timestamp:new Date().toISOString(),tool:activeTool});
        if(activeTool==="Equations") await appendEquationGraph(body,form,result);
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
    const names=title==="Scientific Calculator"?["expression"]:title==="Equations"?["equation","system_equations","expression"]:title==="Graphing Calculator"?["expression"]:title==="Calculus"?["expression","lower","upper","point"]:["expression"];
    const targets=names.map(name=>form.elements.namedItem(name)).filter(Boolean);
    if(!targets.length)return;
    targets.forEach(control=>{control.setAttribute("inputmode","none");control.setAttribute("autocomplete","off");control.setAttribute("autocapitalize","off");});
    const keypad=document.createElement("div");keypad.className="math-keypad";keypad.setAttribute("aria-label","Math input keypad");
    const pages=[
      [["x","x"],["y","y"],["z","z"],["π","pi"],["e","e"],["√(","sqrt("],["sin(","sin("],["cos(","cos("],["tan(","tan("],["log(","log("],["ln(","ln("],["7","7"],["8","8"],["9","9"],["÷","/"],["4","4"],["5","5"],["6","6"],["×","*"],["1","1"],["2","2"],["3","3"],["−","-"],["0","0"],[".","."],["(","("],[")",")"],["^","^"],["+","+"],["=","="],["⌫","BACKSPACE"],["Clear","CLEAR"]],
      [["sin⁻¹","asin("],["cos⁻¹","acos("],["tan⁻¹","atan("],["sinh","sinh("],["cosh","cosh("],["tanh","tanh("],["abs","abs("],["exp","exp("],["√","sqrt("],["∛","cbrt("],["n!","factorial("],["%","%"],["mod","%"],["∞","oo"],[",",","],["⌫","BACKSPACE"],["Clear","CLEAR"]]
    ];
    const switcher=document.createElement("div");switcher.className="keypad-page-switcher";
    const keysWrap=document.createElement("div");keysWrap.className="math-keypad-keys";
    let page=0;
    const draw=()=>{keysWrap.replaceChildren();pages[page].forEach(([label,value])=>{
      const key=document.createElement("button");key.type="button";key.className="math-key";key.textContent=label;key.dataset.mathKey=value;
      key.addEventListener("mousedown",event=>event.preventDefault());
      key.addEventListener("click",()=>{
        const target=targets.find(control=>control===document.activeElement)||targets[0];
        const start=Number.isInteger(target.selectionStart)?target.selectionStart:target.value.length;
        const end=Number.isInteger(target.selectionEnd)?target.selectionEnd:start;
        if(value==="CLEAR"){target.value="";target.setSelectionRange(0,0);}
        else if(value==="BACKSPACE"){const from=start===end?Math.max(0,start-1):start;target.value=target.value.slice(0,from)+target.value.slice(end);target.setSelectionRange(from,from);}
        else{const insert=value==="π"?"π":value;target.setRangeText(insert,start,end,"end");}
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
    const rows=raw.split(/\n|;/).map(row=>row.trim()).filter(Boolean).map(row=>row.split(/[,\s]+/).filter(Boolean).map(token=>{
      if(!/^[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:\/\d+)?$/.test(token))throw new Error("Matrix cells must be numbers or simple fractions such as 3/4.");return token;
    }));
    if(!rows.length||rows.some(row=>row.length!==rows[0].length))throw new Error("Each matrix must be rectangular with the same number of values per row.");
    if(rows.length>8||rows[0].length>8)throw new Error("Matrix dimensions are limited to 8 × 8 by the API.");
    return rows;
  }
  function renderResult(container,result) {
    container.replaceChildren();
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
    } else if(isRecord(result)&&Array.isArray(result.points)){
      const finite=result.points.filter(point=>point&&point.y!==null&&point.y!==undefined&&Number.isFinite(Number(point.x))&&Number.isFinite(Number(point.y)));
      const graphHeading=heading(activeTool==="Graphing Calculator"?"Function graph":"Graph");
      graphHeading.classList.add("graph-result-heading");
      if(finite.length>=2){
        container.append(drawGraph(result.points.map(point=>({x:Number(point.x),y:point.y===null?null:Number(point.y)}))));
      } else {
        const message=document.createElement("p");message.className="result-error";
        message.textContent=result.points.length?"The API returned samples, but fewer than two points have defined real values. Try a different range or function.":"The API returned no graph samples. Please try again.";
        container.append(message);
      }
      row("sample_points",result.points.length);
      row("defined_samples",finite.length);
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
      Object.entries(result).forEach(([key,value])=>{
        if(key==="result"&&(typeof value==="number"||typeof value==="string"))return;
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
    const details=document.createElement("details");details.className="result-raw-details";
    const summary=document.createElement("summary");summary.textContent="Technical response";details.append(summary);
    const pre=document.createElement("pre");pre.className="result-json";pre.textContent=typeof result==="string"?result:JSON.stringify(result,null,2);details.append(pre);container.append(details);
    const copy=button("Copy result","secondary-button","button");
    copy.addEventListener("click",async()=>{const content=pre.textContent;try{await navigator.clipboard.writeText(content);copy.textContent="Copied";}catch{const ta=document.createElement("textarea");ta.value=content;document.body.append(ta);ta.select();const ok=document.execCommand("copy");ta.remove();copy.textContent=ok?"Copied":"Copy unavailable";}});
    container.append(copy);
  }
  function drawGraph(points) {
    const figure=document.createElement("figure");figure.className="graph-figure";
    const width=720,height=360,pad={left:58,right:18,top:18,bottom:42};
    const valid=points.filter(p=>Number.isFinite(p.x)&&Number.isFinite(p.y));
    if(valid.length<2){const msg=document.createElement("figcaption");msg.textContent="Not enough finite samples to draw this graph.";figure.append(msg);return figure;}
    const xmin=Math.min(...valid.map(p=>p.x)),xmax=Math.max(...valid.map(p=>p.x));
    let ymin=Math.min(...valid.map(p=>p.y)),ymax=Math.max(...valid.map(p=>p.y));
    if(xmin===xmax||!Number.isFinite(xmin)||!Number.isFinite(xmax)){const msg=document.createElement("figcaption");msg.textContent="Invalid x-range returned by the API.";figure.append(msg);return figure;}
    if(ymin===ymax){const spread=Math.max(1,Math.abs(ymin)*.1);ymin-=spread;ymax+=spread;}
    if(Math.max(Math.abs(ymin),Math.abs(ymax))>1e6){ymin=Math.max(-1e6,Math.min(1e6,ymin));ymax=Math.max(-1e6,Math.min(1e6,ymax));if(ymin===ymax){ymin-=1;ymax+=1;}}
    const px=x=>pad.left+(x-xmin)/(xmax-xmin)*(width-pad.left-pad.right);
    const py=y=>height-pad.bottom-(y-ymin)/(ymax-ymin)*(height-pad.top-pad.bottom);
    const ns="http://www.w3.org/2000/svg",svg=document.createElementNS(ns,"svg");
    svg.setAttribute("viewBox","0 0 "+width+" "+height);svg.setAttribute("role","img");svg.setAttribute("aria-label","Function graph with labelled axes");
    function line(x1,y1,x2,y2,cls){const el=document.createElementNS(ns,"line");Object.entries({x1,y1,x2,y2}).forEach(([k,v])=>el.setAttribute(k,v));el.setAttribute("class",cls);svg.append(el);}
    function label(x,y,text,anchor="middle",cls="graph-label"){const el=document.createElementNS(ns,"text");el.setAttribute("x",x);el.setAttribute("y",y);el.setAttribute("text-anchor",anchor);el.setAttribute("class",cls);el.textContent=text;svg.append(el);}
    const fmt=v=>Math.abs(v)<1e-8?"0":Number(v.toPrecision(4)).toString();
    for(let i=0;i<=4;i++){const xv=xmin+(xmax-xmin)*i/4,x=px(xv);line(x,pad.top,x,height-pad.bottom,"graph-grid");label(x,height-pad.bottom+20,fmt(xv));const yv=ymin+(ymax-ymin)*i/4,y=py(yv);line(pad.left,y,width-pad.right,y,"graph-grid");label(pad.left-9,y+4,fmt(yv),"end");}
    if(xmin<=0&&xmax>=0)line(px(0),pad.top,px(0),height-pad.bottom,"graph-axis");
    if(ymin<=0&&ymax>=0)line(pad.left,py(0),width-pad.right,py(0),"graph-axis");
    let d="",active=false,previousY=null;
    points.forEach(p=>{if(!Number.isFinite(p.x)||!Number.isFinite(p.y)||p.y<ymin||p.y>ymax){active=false;previousY=null;return;}if(previousY!==null&&Math.abs(p.y-previousY)>(ymax-ymin)*.7)active=false;d+=(active?"L":"M")+px(p.x).toFixed(2)+","+py(p.y).toFixed(2)+" ";active=true;previousY=p.y;});
    const path=document.createElementNS(ns,"path");path.setAttribute("d",d);path.setAttribute("class","graph-curve");svg.append(path);
    label((pad.left+width-pad.right)/2,height-6,"x","middle","graph-axis-title");
    const yt=document.createElementNS(ns,"text");yt.setAttribute("x","15");yt.setAttribute("y",height/2);yt.setAttribute("transform","rotate(-90 15 "+(height/2)+")");yt.setAttribute("class","graph-axis-title");yt.setAttribute("text-anchor","middle");yt.textContent="y";svg.append(yt);
    figure.append(svg);const caption=document.createElement("figcaption");caption.textContent="x: "+fmt(xmin)+" to "+fmt(xmax)+" · y viewport: "+fmt(ymin)+" to "+fmt(ymax);figure.append(caption);return figure;
  }
  function equationGraphExpression(raw) {
    const normalized=String(raw).replaceAll("²","^2").replaceAll("³","^3").replace(/[−–]/g,"-").replace(/[×·]/g,"*").replaceAll("÷","/");
    const parts=normalized.split("=");if(parts.length>2||!parts[0]?.trim())return null;
    // A 2D graph of a multivariable relation is a slice: hold y and z at zero,
    // then plot the left-minus-right residual against x. Its zero crossings
    // show solutions along that slice, not the entire higher-dimensional set.
    const expression=(parts.length===2?"("+parts[0]+")-("+parts[1]+")":parts[0])
      .replace(/\by\b/gi,"0").replace(/\bz\b/gi,"0");
    if(!/^[0-9xX+*/^().\s-]+$/.test(expression))return null;
    return expression;
  }
  async function appendEquationGraph(container,form,result) {
    const mode=val(form,"equation_mode");
    const section=document.createElement("section");section.className="equation-graph-section";
    const heading=document.createElement("h3");heading.textContent="Equation graph";section.append(heading);
    const note=document.createElement("p");note.className="field-help";
    note.textContent=mode==="system"
      ?"The graph shows the first equation as a 2D slice; a full system may require multiple plots."
      :"For equations with multiple variables, y and z are fixed at 0 and the equation residual is plotted against x. This is a 2D slice, not the full relation.";
    section.append(note);container.append(section);
    if(mode==="binomial"){
      const message=document.createElement("p");message.className="field-help";
      message.textContent="A binomial expansion is an expression rather than an equation. Convert it into an equation to plot it.";
      section.append(message);return;
    }
    let raw=val(form,"equation");
    if(mode==="system")raw=val(form,"system_equations").split(/\n+/).map(line=>line.trim()).filter(Boolean)[0]||"";
    const expression=equationGraphExpression(raw);
    if(!expression){const msg=document.createElement("p");msg.className="field-help";msg.textContent="This equation could not be plotted with the current 2D graph engine. The equation result is still available above.";section.append(msg);return;}
    let x_min,x_max;
    try{x_min=number(form,"graph_x_min");x_max=number(form,"graph_x_max");}
    catch{ x_min=-10; x_max=10; }
    if(!Number.isFinite(x_min)||!Number.isFinite(x_max)||x_min>=x_max){x_min=-10;x_max=10;}
    try{
      const sampled=await api("/api/v1/graph/sample",{expression,x_min,x_max,points:401});
      if(Array.isArray(sampled.points)&&sampled.points.length) {
        section.append(drawGraph(sampled.points));
        const caption=document.createElement("p");caption.className="field-help";caption.textContent="x range: "+x_min+" to "+x_max+". Zeros of the plotted residual indicate solutions in this slice.";section.append(caption);
      } else {
        const msg=document.createElement("p");msg.className="field-help";msg.textContent="No graph samples were returned. The equation result is still available above.";section.append(msg);
      }
    }catch(error){const msg=document.createElement("p");msg.className="field-help";msg.textContent="Graph unavailable for this equation: "+error.message;section.append(msg);}
  }
  function transformDegreeTrig(expression) {
    expression=expression.replace(/π/g,"pi");
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
      case "Equations": {
        const mode=val(form,"equation_mode");
        if(mode==="binomial")return api("/api/v1/binomials/expand",{expression:val(form,"expression")});
        if(mode==="system")return api("/api/v1/equations/system",{equations:val(form,"system_equations").split(/\n+/).map(line=>line.trim()).filter(Boolean)});
        const equation=val(form,"equation");
        if(!equation.includes("="))throw new Error("Enter an equation with an equals sign, for example x^2 + y = 5.");
        return api("/api/v1/equations/solve",{equation, equation_type:mode});
      }
      case "Graphing Calculator": {const x_min=number(form,"x_min"),x_max=number(form,"x_max"),points=integer(form,"points");if(x_min>=x_max)throw new Error("Maximum x must be greater than minimum x.");if(points<2||points>2000)throw new Error("Sample points must be between 2 and 2,000.");let expression=val(form,"expression").replace(/[−–]/g,"-").trim();if(/^\s*(?:x\s*=\s*y|y\s*=\s*x)\s*$/i.test(expression))expression="x";return api("/api/v1/graph/sample",{expression,x_min,x_max,points});}
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
      case "Unit Converter": {const mode=val(form,"conversion_type");if(mode==="currency")return api("/api/v1/currency/convert",{amount:number(form,"amount"),from_currency:val(form,"from_currency").toUpperCase(),to_currency:val(form,"to_currency").toUpperCase()});if(mode==="base")return api("/api/v1/numbers/convert-base",{value:val(form,"base_value"),from_base:integer(form,"from_base"),to_base:integer(form,"to_base")});return api("/api/v1/units/convert",{value:number(form,"value"),from_unit:val(form,"from_unit"),to_unit:val(form,"to_unit")});}
      case "Finance & Loan EMI": {const op=val(form,"operation");if(op==="simple-interest")return api("/api/v1/finance/simple-interest",{principal:number(form,"principal"),annual_rate:number(form,"annual_rate"),years:number(form,"years")});if(op==="compound-interest")return api("/api/v1/finance/compound-interest",{principal:number(form,"principal"),annual_rate:number(form,"annual_rate"),years:number(form,"years"),compounding_per_year:integer(form,"compounding_per_year")});return api("/api/v1/finance/emi",{principal:number(form,"principal"),annual_rate:number(form,"annual_rate"),tenure_months:integer(form,"tenure_months")});}
      case "Discount & GST Calculator": {if(val(form,"operation")==="discount")return api("/api/v1/discount/calculate",{price:number(form,"price"),discount_percent:number(form,"discount_percent")});return api("/api/v1/gst/calculate",{amount:number(form,"price"),gst_rate:number(form,"gst_rate"),inclusive:val(form,"inclusive")==="true"});}
      case "BMI Calculator": return api("/api/v1/health/bmi",{weight_kg:number(form,"weight_kg"),height_m:number(form,"height_m")});
      case "Date Calculator": {const operation=val(form,"operation"),payload={operation,date:val(form,"date"),days:integer(form,"days")||0};if(operation==="difference")payload.other_date=val(form,"other_date");return api("/api/v1/dates/calculate",payload);}
      default: throw new Error("This tool is not configured yet.");
    }
  }

  function renderTool(title) {
    if(title==="Quadratic & Polynomial Solver" || title==="Binomial Expansion") title="Equations";
    activeTool=title;pageTitle.textContent=title;workspaceTitle.textContent=title;workspaceSubtitle.textContent=descriptions[title]||"";
    angleToggle.hidden=title!=="Scientific Calculator";
    navItems.forEach(item=>{const selected=item.dataset.tool===title;item.classList.toggle("is-active",selected);if(selected)item.setAttribute("aria-current","page");else item.removeAttribute("aria-current");});
    setDrawer(false);if(title==="Scientific Calculator"){scientificWorkspace();return;}
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
      ])]],["Single equation",[txt("equation","Equation","","e.g. xy + yz = 3x^2yz","Use an equals sign. General polynomial mode accepts mixed terms and any degree in x, y, and z."),num("graph_x_min","Graph minimum x","-10"),num("graph_x_max","Graph maximum x","10")]],["System of equations",[area("system_equations","Equations (one per line)","x + y = 5\ny - x = 1","Enter each equation on a separate line.")]],["Binomial expansion",[txt("expression","Binomial expression","","e.g. (x + 2)^3")]]];break;
      case "Graphing Calculator":spec=[["Function",[txt("expression","Function of x","","e.g. sin(x) or x^2 - 4"),num("x_min","Minimum x","-10"),num("x_max","Maximum x","10"),num("points","Sample points","401","Choose 2–2,000 points. More samples can make curves smoother.")]]];break;
      case "Calculus":spec=[["Calculus operation",[sel("operation","Operation",selectOptions.calculusOperation),sel("variable","Variable",options(["x","y","z","t"])),num("order","Derivative order","1"),txt("expression","Expression","","e.g. x^3 + sin(x)"),txt("lower","Lower bound","0"),txt("upper","Upper bound","1"),txt("point","Limit point","0"),sel("direction","Limit direction",options(["both","plus","minus"]))]]];break;
      case "Matrix Calculator":spec=[["Matrix operation",[sel("operation","Matrix operation",selectOptions.matrixOperation),area("matrix_a","Matrix A","1, 2\n3, 4","Rows separated by new lines; values separated by commas."),area("matrix_b","Matrix B","5, 6\n7, 8","Required for add, subtract, multiply, and compare."),txt("scalar","Scalar","2"),num("power","Power","2"),num("size","Size for identity/zero","3"),num("row","Row (1-based)","1"),num("column","Column (1-based)","1"),area("vector","Vector b","5, 11","For solving Ax = b; values separated by commas."),sel("method","Inverse method",[["","Default"],["adjoint","Adjoint"],["gauss_jordan","Gauss–Jordan"]]),sel("steps","Step-by-step working",[["false","Off"],["true","On"]])]]];break;
      case "Statistics":spec=[["Dataset",[sel("operation","Statistic",selectOptions.statsOperation),area("values","Values","12, 15, 18, 18, 21","Separate observations with commas, spaces, or new lines.")]]];break;
      case "Probability & Combinatorics":spec=[["Probability or counting inputs",[sel("operation","Operation",selectOptions.probabilityOperation),num("favorable","Favourable outcomes","1"),num("total","Total outcomes","6"),num("event_a","P(A)","0.5"),num("event_b","P(B)","0.4"),num("intersection","P(A ∩ B)","0.2"),num("n","n","5"),num("r","r","2"),num("p","Success probability p","0.5"),num("k","Successes k","2")]]];break;
      case "Unit Converter":{const dims=capabilities?.unit_dimensions||[],fallback=[{id:"length",units:["m","cm","km","mm","ft","in"]},{id:"mass",units:["kg","g","mg","lb","oz"]},{id:"temperature",units:["celsius","fahrenheit","kelvin"]},{id:"time",units:["s","min","h","day"]},{id:"volume",units:["L","mL"]}];const categories=dims.length?dims:fallback;const categoryOptions=categories.map(d=>[d.id,d.id.replaceAll("_"," ").replace(/\b\w/g,c=>c.toUpperCase())]);const initial=categories[0];const unitOptions=initial.units.map(unit=>[unit,String(unit).replaceAll("_"," ").replace(/\b\w/g,c=>c.toUpperCase())]);spec=[["Conversion type",[sel("conversion_type","What do you want to convert?",[["units","Physical units"],["currency","Currency"],["base","Number base"]])]],["Unit category",[sel("dimension","Unit category",categoryOptions)]],["Unit conversion",[num("value","Value","1"),sel("from_unit","From unit",unitOptions),sel("to_unit","To unit",unitOptions)]],["Currency conversion",[num("amount","Amount","100"),sel("from_currency","From currency",options(["INR","USD","EUR","GBP","JPY","CAD","AUD","CNY","SGD","AED"])),sel("to_currency","To currency",options(["USD","INR","EUR","GBP","JPY","CAD","AUD","CNY","SGD","AED"]))]],["Number base conversion",[txt("base_value","Integer value","255","e.g. 255 or FF"),num("from_base","From base","10"),num("to_base","To base","16")]]];break;}
      case "Finance & Loan EMI":spec=[["Finance calculation",[sel("operation","Calculation",selectOptions.financeOperation),num("principal","Principal / loan amount","100000"),num("annual_rate","Annual interest rate (%)","8.5"),num("years","Term (years)","5"),num("compounding_per_year","Compounds per year","12"),num("tenure_months","Loan tenure (months)","60")]]];break;
      case "Discount & GST Calculator":spec=[["Discount or GST",[sel("operation","Calculation",[["discount","Discount"],["gst","GST"]]),num("price","Price / amount","1000"),num("discount_percent","Discount (%)","10"),num("gst_rate","GST rate (%)","18"),sel("inclusive","GST amount includes tax?",[["false","No — add GST"],["true","Yes — extract GST"]])]]];break;
      case "BMI Calculator":spec=[["Body measurements",[num("weight_kg","Weight (kg)","70"),num("height_m","Height (metres)","1.75")]]];break;
      case "Date Calculator":spec=[["Date calculation",[sel("operation","Operation",selectOptions.dateOperation),field("date","Date",{type:"text",value:new Date().toISOString().slice(0,10),help:"Use YYYY-MM-DD."}),num("days","Number of days","7"),field("other_date","Second date",{type:"text",value:new Date().toISOString().slice(0,10),help:"Only used for date difference; YYYY-MM-DD."})]]];break;
    }
    const {form}=createPanel(title,descriptions[title]);addFields(form,spec);
    if(["Scientific Calculator","Equations","Graphing Calculator","Calculus"].includes(title)) addMathKeypad(form,title);
    if(title==="Equations"){
      const mode=form.elements.equation_mode;
      const updateEquationMode=()=>{
        const selected=mode.value,system=selected==="system",binomial=selected==="binomial";
        form.elements.equation.closest(".field").hidden=system||binomial;
        form.elements.graph_x_min.closest(".field").hidden=system||binomial||!selected.includes("quadratic");
        form.elements.graph_x_max.closest(".field").hidden=system||binomial||!selected.includes("quadratic");
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
      const help=document.createElement("small");help.className="field-help";help.id="graph-expression-help";help.textContent="Enter a function of x, such as x^2, sin(x), or 1/x. Press Calculate to draw the graph below.";
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
    if(title==="Date Calculator"){
      const op=form.elements.operation;const update=()=>{form.elements.days.closest(".field").hidden=op.value==="difference";form.elements.other_date.closest(".field").hidden=op.value!=="difference";};op.addEventListener("change",update);update();
    }
  }
  navItems.forEach(item=>item.addEventListener("click",()=>renderTool(item.dataset.tool)));
  renderTool(activeTool);checkApi();
})();