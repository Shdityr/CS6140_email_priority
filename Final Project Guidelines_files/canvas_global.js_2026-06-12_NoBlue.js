
////////////////////////////////////////////////////////////////////
//
//  Canvas Prod Global Javascript file                        
//                                         
//  Updates:                                
//
//  2020-05-27 Added Blackboard Ally code - CC 
//  2020-06-05 Added additional Cidilabs user - SH
//  2020-06-08 Modified Ally code per vendor instructions - CC
//  2020-06-19 Modified Cidilabs code to deploy for all users hidden - CC
//  2020-07-02 Added Evalkit Javascript
//  2020-07-15 Deleted Evalkit section because it has been moved to CPS Theme javascript file only
//  2020-08-24 Moved Ally code up a little (above Motimatic)
//  2020-10-20 Updated Motimatic code from vendor email
//  2021-02-15 added code to hide view ungraded as 0 feature - Samy
//  2021-04-12 added Cidilabs code to override Ally headings (overrideAllyHeadings: true)
//  2021-06-08 added Cidilabs code to show student cards (showStudentCards: true)
//  2021-06-09 added Cidilabs code to make rubrics sortable (sortableRubrics: true)
//  2021-08-09 prohibit full name editing by graying out fields
//  2021-11-19 inactive labels in roster changed to say "inactive (dropped)"
//  2022-04-28 temporarily removed Eesysoft JS in order to fix Discussion Board problem
//  2022-05-11 restored Eesysoft JS in response to report from vendor that discussion board reply issue is fixed
//  2022-12-07 prettied up this document a bit, standardizing the dividers ---------- CC
//  2023-03-10 added 2nd link to google analytics for the one managed by ITS, links to GA4 version
//  2023-08-31 added Cidi Labs code for new DesignPLUS sidebar - EBP
//  2024-01-24 default Cidi Labs to new Sidebar for DesignPLUS - EBP
//  2024-01-31 removed Eesysoft JS for Plugin method
//  2024-05-06 removed Ally section (deploying UDOIT in its place) - CC
//  2024-05-17 redirect x-list button by "crosslist_link" class to service-now form - SH
//  2024-06-03 Added student access to UDOIT per instructions https://udoit3.ciditools.com/student/setup - CC
//  2024-06-12 Replaced student access to UDOIT code with new code from vendor to fix a bug - CC
//  2025-03-25 Added Explorance Blue section
//  2026-03-03 Updated DesignPLUS code per instructions https://tinyurl.com/3pjkr7f5 - CC
//  2026-06-12 Removed Explorance Blue to test if it is causing issues
//
////////////////////////////////////////////////////////////////////

/*jslint es6 */







// --------------------------------------------






/*********************** 
* Start UDOIT Student * 
***********************/ 

UdoitConfig = { 
supportedAlternates: ['pdf', 'html', 'mp3', 'epub', 'txt'], 
allowAlternateRequest: true, 
enabledByDefault: true, 
} 

function loadUdoitScript() { 
if (!UdoitConfig.toolUri) { 
UdoitConfig.toolUri = 'https://udoit3.ciditools.com'; 
} 
let script = document.createElement('script'), 
firstScript = document.getElementsByTagName('script')[0] 
script.src = UdoitConfig.toolUri + '/build/studentController.js' 
script.crossOrigin = 'anonymous' 
if (null !== firstScript.parentNode) { 
firstScript.parentNode.insertBefore(script, firstScript) 
console.log('udoit student controller added') 
} 
} 

function checkForUdoit() { 
let body = document.getElementsByTagName('body')[0] 
if (!body.className.includes('udoit-student-loaded')) { 
loadUdoitScript() 
body.className += ' udoit-student-loaded' 
} 
} 
checkForUdoit() 
/*** END UDOIT Student ***/ 







// --------------------------------------------






////////////////////////////////////////////////////
// DESIGNPLUS CONFIG                            //
////////////////////////////////////////////////////

// Legacy

var DT_variables = {
    iframeID: '',
    // Path to the hosted USU Design Tools
    path: 'https://designtools.ciditools.com/',
    templateCourse: '626',
    // OPTIONAL: Transform people page in a course to show student cards
    showStudentCards: true,
    // OPTIONAL: Make assignment rubrics sortable
    sortableRubrics: true,
    // OPTIONAL: Relocate Ally alternative formats dropdown and hide heading
    overrideAllyHeadings: true,
    // OPTIONAL: Button will be hidden from view until launched using shortcut keys
    hideButton: true,
     // OPTIONAL: Limit by course format
     limitByFormat: false, // Change to true to limit by format
     // adjust the formats as needed. Format must be set for the course and in this array for tools to load
     formatArray: [
        'online',
        'on-campus',
        'blended'
    ],
    // OPTIONAL: Limit tools loading by users role
    limitByRole: false, // set to true to limit to roles in the roleArray
    // adjust roles as needed
    roleArray: [
        'student',
        'teacher',
        'admin'
    ],
    // OPTIONAL: Limit tools to an array of Canvas user IDs
    limitByUser: false, // Change to true to limit by user
    // add users to array (Canvas user ID not SIS user ID)
    userArray: [
        '81862', // Abby Felony
        '81861', // AJ Dalal
        '90', // Alyssa Faria
        '96', // Cathy Swain
        '85', // Chris Carrillo
        '80005', // Chris Cutno
        '92', // Clair Waterbury
        '38823', // Denise Litlefield
        '80010', // Dominique Lieu
        '82413', // Donisa Norman
        '79598', // Emma Zelenko
        '128', // Erin Rosas
        '109', // Jackie Bishop
        '101', // James Lewis
        '52923', // Jennifer Pope
        '91', // Jesse Savage
        '57485', // Joe Ryan
        '80831', // John McDonough
        '79392', // Jonathan Quint
        '11081', // Kate Chan
        '87', // Lauren Hankin
        '94', // Lindsey Sudbury
        '234', // Maria Valencia-Devin
        '961', // Nina Araujo
        '171', // Samy Hay
        '123', // Sarah Callan
        '89', // Sarah Cochran
        '88', // Stephanie Gary
        '126', // Todd Relaford
        '214', // Jamie Traynor
        '19779', // Will Frasca
        '66907', //  Joe Venezia
        '19911', // Melissa Frazier
        '13910', // Dave Crowley
        '24998', // Teri Hall
    '48001', //Shane O'Connor
    '25384',//Jeremy Hamilton
        '56633', // Rebecca Rufo-Tepper
        '217', // Erin Provensal
        '85140', //Kate Tullio
    '41877' // Cindy Masters
    ]
};


// New

window.DpConfig = window.DpConfig || {
lms: 'canvas',
templateCourse: '163606',
hideButton: true,
extendedCourse: '', // added in sub-account theme
sharedCourse: '', // added from localStorage
courseFormats: [],
canvasRoles: [],
canvasUsers: [],
canvasCourseIds: [],
plugins: [],
excludedModules: [],
includedModules: [],
lang: 'en',
defaultToLegacy: false,
enableVersionSwitching: true,
}


// Merge with any extended configurations
if (window.DpExtended) {
    window.DpConfig = { ...window.DpConfig, ...window.DpExtended };
}

// Minimal script loader with caching support
(function () {
    // Determine environment and base URI
    const uriPrefix = (location.href.includes('.beta.')) ? 'beta.' : '';
    const toolsUri = (window.DpConfig.toolsUri) ? window.DpConfig.toolsUri : `https://designplus.${uriPrefix}ciditools.com/`;

    // Function to load script with version
    function loadScript(version) {
        const script = document.createElement('script');
        script.src = `${toolsUri}js/controller.js?v=${version}`;
        script.crossOrigin = 'anonymous';
        script.async = true;
        script.onerror = () => console.error('DesignPlus: Failed to load main application script');

        const firstScript = document.getElementsByTagName('script')[0];
        firstScript.parentNode.insertBefore(script, firstScript);

        console.log(`DesignPlus: Loading application v${version} from ${script.src}`);
    }

    // Try to fetch version info for cache busting
    fetch(`${toolsUri}js/version.json?t=${Date.now()}`)
        .then(response => response.ok ? response.json() : null)
        .then(versionInfo => {
            const version = (versionInfo && versionInfo.version) ? versionInfo.version : Date.now();
            window.DpConfig.version = version;
            loadScript(version);
        })
        .catch(() => {
            // Fallback to timestamp-based versioning
            const fallbackVersion = Date.now();
            window.DpConfig.version = fallbackVersion;
            loadScript(fallbackVersion);
        });
})();



////////////////////////////////////////////////////
// END DESIGNPLUS CONFIG                        //
////////////////////////////////////////////////////









// --------------------------------------------










// Change "inactive" label on enrollments to "inactive (dropped)"
'use strict';

const waitForElement = (querySelector, timeout) => {
return new Promise((resolve, reject) => {
let timer = false;
if (document.querySelectorAll(querySelector).length) return resolve();
const observer = new MutationObserver(() => {
  if (document.querySelectorAll(querySelector).length) {
    observer.disconnect();
    if (timer !== false) clearTimeout(timer);
    return resolve();
  }
});
observer.observe(document.body, { childList: true, subtree: true });
if (timeout)
  timer = setTimeout(() => {
    observer.disconnect();
    reject();
  }, timeout);
});
};

window.onload = () => {
if (window.location.pathname === `/courses/${ENV?.course?.id}/users` ) {
waitForElement('table.roster', 3000).then(function () {
  let inactiveLabels = document.querySelectorAll("span.label[title$='not able to access the course']");
  for (const label of inactiveLabels) {
    label.innerHTML = 'inactive (dropped)';
  }
});
}else if (window.location.pathname === `/courses/${ENV?.course?.id}/gradebook`) {
waitForElement('span.label[title$="not able to access the course"]', 3000).then(function () {
  let inactiveLabels = document.querySelectorAll("span.label[title$='not able to access the course']");
  for (const label of inactiveLabels) {
    label.innerHTML = 'inactive (dropped)';
  }
});
}  
};





// --------------------------------------------







// Explorance Blue added 2025-03-25

/*
var BLUE_CANVAS_SETUP={connectorUrl:"https://northeastern-integration.bluera.com/northeasternBlueConnector/",canvasAPI:window.location.origin,domainName:"com.explorance",consumerID:"uneAb3wY2QaWRG4D4S117w==",defaultLanguage:"en-us"},BlueCanvasJS=document.createElement("script");BlueCanvasJS.setAttribute("type","text/javascript");BlueCanvasJS.setAttribute("src","https://northeastern-integration.bluera.com/northeasternBlueConnector//Scripts/Canvas/BlueCanvas.min.js");BlueCanvasJS.async=!0;document.getElementsByTagName("head")[0].appendChild(BlueCanvasJS);
*/






// --------------------------------------------






// Inject text under local login page indicating it is the local admin login page

$(document).ready(function() {
if (document.URL == 'https://northeastern.instructure.com/login/canvas') {
  document.getElementById("footer").innerHTML = '<h5>This is the ADMIN login page for Canvas. To login to Canvas as a Student or Instructor, please go to </h5><b><h2 align="center"><a href="http://northeastern.instructure.com">northeastern.instructure.com</a></b></h2>';
}





// --------------------------------------------






// make xlist link redirect to snow form
document.getElementsByClassName('crosslist_link')[0].setAttribute('href', 'https://service.northeastern.edu/tech?id=sc_cat_item&sys_id=e82d7164dbdae0102d2caa82ca961922');
document.getElementsByClassName('crosslist_link')[0].setAttribute('target','_blank');
document.getElementsByClassName('crosslist_link')[0].classList.remove('crosslist_link');
});






// --------------------------------------------







// Don't let non-admins delete, reset, or conclude courses

$(document).ready(function() {
if(ENV.current_user_roles.indexOf('teacher') > -1 && ENV.current_user_roles.indexOf('admin') == -1){
    $("a.Button:contains('Reset Course Content')").remove();
    $("a.Button:contains('Delete this Course')").remove();
    $("a.Button:contains('Conclude this Course')").remove();
  }
});






// --------------------------------------------






// Google Analytics

function removeStorage(e){try{localStorage.removeItem(e),localStorage.removeItem(e+"_expiresIn")}catch(t){return console.log("removeStorage: Error removing key ["+e+"] from localStorage: "+JSON.stringify(t)),!1}return!0}function getStorage(e){var t=Date.now(),o=localStorage.getItem(e+"_expiresIn");if(null==o&&(o=0),o<t)return removeStorage(e),null;try{return localStorage.getItem(e)}catch(t){return console.log("getStorage: Error reading key ["+e+"] from localStorage: "+JSON.stringify(t)),null}}function setStorage(e,t,o){o=null==o?86400:Math.abs(o);var s=Date.now()+1e3*o;try{localStorage.setItem(e,t),localStorage.setItem(e+"_expiresIn",s)}catch(t){return console.log("setStorage: Error setting key ["+e+"] in localStorage: "+JSON.stringify(t)),!1}return!0}async function coursesRequest(e){let t=await fetch("/api/v1/users/self/courses?per_page=100"),o=await t.text();o=o.substr(9),o=JSON.parse(o);var s=JSON.stringify(o);return setStorage("ga_enrollments",s,null),parseCourses(e,s)}function parseCourses(e,t){if(null!=t){let s=JSON.parse(t);for(var o=0;o<s.length;o++)if(s[o].id==e)return s[o]}return null}function gaCourseDimensions(e){custom_ga("set","dimension4",e.id),custom_ga("set","dimension5",e.name),custom_ga("set","dimension6",e.account_id),custom_ga("set","dimension7",e.enrollment_term_id),custom_ga("set","dimension8",e.enrollments[0].type),custom_ga("send","pageview")}function googleAnalyticsCode(e){var t,o,s,n;if(custom_ga("create",e,"auto"),t=ENV.current_user_id,o=ENV.current_user_roles,custom_ga("set","userId",t),custom_ga("set","dimension1",t),custom_ga("set","dimension3",o),n=window.location.pathname.match(/\/courses\/(\d+)/)){n=n[1],s=0;try{let e=getStorage("ga_enrollments");if(null!=e){var r=parseCourses(n,e);null===r?coursesRequest(n).then(e=>{null===e?(custom_ga("set","dimension4",n),custom_ga("send","pageview")):gaCourseDimensions(e)}):gaCourseDimensions(r)}else coursesRequest(n).then(e=>{null===e?(custom_ga("set","dimension4",n),custom_ga("send","pageview")):gaCourseDimensions(e)})}catch(e){if((s+=1)>5)return custom_ga("set","dimension4",n),void custom_ga("send","pageview")}}else custom_ga("send","pageview")}!function(e,t,o,s,n,r,a){e.GoogleAnalyticsObject=n,e[n]=e[n]||function(){(e[n].q=e[n].q||[]).push(arguments)},e[n].l=1*new Date,r=t.createElement(o),a=t.getElementsByTagName(o)[0],r.async=1,r.src="https://www.google-analytics.com/analytics.js",a.parentNode.insertBefore(r,a)}(window,document,"script",0,"custom_ga");
googleAnalyticsCode("UA-47018607-3"); // customize google analytics tracking number here


// google analytics for the rest of ITS people
(function(w,d,s,l,i){w[l]=w[l]||[];w[l].push({'gtm.start':
new Date().getTime(),event:'gtm.js'});var f=d.getElementsByTagName(s)[0],
j=d.createElement(s),dl=l!='dataLayer'?'&l='+l:'';j.async=true;j.src=
'https://www.googletagmanager.com/gtm.js?id='+i+dl;f.parentNode.insertBefore(j,f);
})(window,document,'script','dataLayer','GTM-WGQLLJ');







// --------------------------------------------






// Rubric importer

// ==UserScript==
// @name        Rubric Importer
// @namespace   https://github.com/jamesjonesmath/canvancement
// @description Create a rubric by copying from a spreadsheet and pasting into Canvas
// @include     https://*.instructure.com/courses/*/rubrics
// @include     https://*.instructure.com/accounts/*/rubrics
// @version     5
// @grant       none
// ==/UserScript==

(function() {
'use strict';
var assocRegex = new RegExp('^/(course|account)s/([0-9]+)/rubrics$');
var errors = [];
var outcomes = [];
var pendingOutcomes = 0;
var criteria = [];
var rubricTitle;
var rubricAssociation;

if (assocRegex.test(window.location.pathname)) {
add_button();
}

function checkPointsRow(cols) {
if (typeof cols === 'undefined' || cols.length < 3 || isPoints(cols[0])) {
  return false;
}
var points = [];
var isValid = true;
var i = 1;
var firstCol;
var block = false;
while (isValid && i < cols.length) {
  var item = cols[i++];
  if (isPoints(item)) {
    points.push(item);
    if (typeof firstCol === 'undefined') {
      firstCol = i - 1;
    }
  } else if (i > 2) {
    isValid = false;
  }
}
if (isValid && points.length > 1) {
  var order = checkMonotonic(points, true);
  if (order) {
    block = {
      'order' : order,
      'points' : points,
      'start' : firstCol,
      'end' : firstCol + points.length - 1,
      'columns' : cols.length
    };
    if (typeof checkPointsRow.initial === 'undefined') {
      checkPointsRow.initial = block.start;
    }
  }
}
return block;
}

function checkMonotonic(A, isStrict) {
if (typeof A === 'undefined') {
  return 0;
}
if (typeof isStrict === 'undefined') {
  isStrict = true;
}
var order;
var isMonotonic = true;
var a, b;
a = Number(A[0]);
var k = 1;
while (isMonotonic && k < A.length) {
  b = Number(A[k]);
  k++;
  var diff = b - a;
  a = b;
  if (Math.abs(diff) < 0.000001) {
    if (isStrict) {
      isMonotonic = false;
    }
  } else {
    if (typeof order === 'undefined') {
      order = diff < 0 ? -1 : 1;
    } else {
      if (order * (diff < 0 ? -1 : 1) < 0) {
        isMonotonic = false;
      }
    }
  }
}
if (typeof order === 'undefined') {
  order = 0;
}
return isMonotonic ? order : 0;
}

function addRubric(title, criteria, association) {
var pointsPossible = 0;
for (var i = 0; i < criteria.length; i++) {
  if (typeof criteria[i].ignore_for_scoring === 'undefined' || !getBoolean(criteria[i].ignore_for_scoring)) {
    pointsPossible += Number(criteria[i].ratings[0].points);
  }
}
var F = {
  'rubric' : {
    'title' : title,
    'points_possible' : pointsPossible,
    'free_form_criterion_comments' : 0,
    'criteria' : criteria,
  },
  'rubric_association' : {
    'id' : '',
    'use_for_grading' : 0,
    'hide_score_total' : 0,
    'association_type' : association.type,
    'association_id' : association.id,
    'purpose' : 'bookmark'
  },
  'title' : title,
  'points_possible' : pointsPossible,
  'rubric_id' : 'new',
  'rubric_association_id' : '',
  'skip_updating_points_possible' : 0,
};
return F;
}

function addCriterion(item) {
if (typeof item === 'undefined') {
  return false;
}
var name = item.name.replace(/\s*\\n\s*/g, ' ').replace(/\s+/g, ' ');
var longDesc = typeof item.longDesc === 'undefined' ? '' : item.longDesc.replace(/\\n/g, '\n');
var ratings = addRatings(item.ratings, item.points);
var criterion = {
  'description' : name,
  'long_description' : longDesc
};
if (ratings !== false) {
  criterion.ratings = ratings;
  criterion.points = ratings[0].points;
}
if (item.outcome !== false) {
  criterion.learning_outcome_id = item.outcome.id;
  if (typeof item.outcome.ignore !== 'undefined' && item.outcome.ignore) {
    criterion.ignore_for_scoring = 1;
  }
}
return criterion;
}

function addRatings(descriptions, points) {
// Generate the ratings, reversing the order if necessary
if (descriptions.length === 0 || descriptions.length !== points.length) {
  return false;
}
var mono = checkMonotonic(points, false);
if (mono === 0) {
  return false;
}
var ratings = [];
var n = points.length;
var j;
for (var i = 0; i < n; i++) {
  j = mono < 0 ? i : n - 1 - i;
  ratings.push({
    'description' : descriptions[j].replace(/\\n/g, ' ').replace(/\s+/g, ' '),
    'points' : points[j],
  });
}
return ratings;
}

function getCsrfToken() {
var csrfRegex = new RegExp('^_csrf_token=(.*)$');
var csrf;
var cookies = document.cookie.split(';');
for (var i = 0; i < cookies.length; i++) {
  var cookie = cookies[i].trim();
  var match = csrfRegex.exec(cookie);
  if (match) {
    csrf = decodeURIComponent(match[1]);
    break;
  }
}
return csrf;
}

function add_button() {
var parent = document.querySelector('aside#right-side');
if (parent) {
  var el = parent.querySelector('#jj_rubric');
  if (!el) {
    el = document.createElement('a');
    el.classList.add('btn', 'button-sidebar-wide');
    el.id = 'jj_rubric';
    var icon = document.createElement('i');
    icon.classList.add('icon-import');
    el.appendChild(icon);
    var txt = document.createTextNode(' Import Rubric');
    el.appendChild(txt);
    el.addEventListener('click', openDialog);
    parent.appendChild(el);
  }
}
}

function createDialog() {
var el = document.querySelector('#jj_rubric_dialog');
if (!el) {
  el = document.createElement('div');
  el.id = 'jj_rubric_dialog';
  el.classList.add('ic-Form-control');
  var label = document.createElement('label');
  label.htmlFor = 'jj_rubric_title';
  label.textContent = 'Rubric Title: ';
  label.classList.add('ic-Label');
  el.appendChild(label);
  var input = document.createElement('input');
  input.id = 'jj_rubric_title';
  input.classList.add('ic-Input');
  input.type = 'text';
  input.placeholder = 'Enter name of rubric';
  el.appendChild(input);
  label = document.createElement('label');
  label.htmlFor = 'jj_rubric_text';
  label.textContent = 'Rubric Contents';
  label.classList.add('ic-Label');
  el.appendChild(label);
  var textarea = document.createElement('textarea');
  textarea.id = 'jj_rubric_text';
  textarea.classList.add('ic-Input');
  textarea.placeholder = 'Paste a tab-delimited rubric into this textbox.';
  el.appendChild(textarea);
  var msg = document.createElement('div');
  msg.id = 'jj_rubric_msg';
  msg.classList.add('ic-flash-warning');
  msg.style.display = 'none';
  el.appendChild(msg);
  var parent = document.querySelector('body');
  parent.appendChild(el);
}
}

function openDialog() {
try {
  createDialog();
  $('#jj_rubric_dialog').dialog({
    'title' : 'Import Rubric',
    'autoOpen' : false,
    'buttons' : [ {
      'text' : 'Create',
      'click' : processDialog
    }, {
      'text' : 'Cancel',
      'click' : function() {
        $(this).dialog('close');
        var el = document.getElementById('jj_rubric_text');
        if (el) {
          el.value = '';
        }
        errors = [];
        updateMsgs();
      }
    } ],
    'modal' : true,
    'height' : 'auto',
    'width' : '80%'
  });
  if (!$('#jj_rubric_dialog').dialog('isOpen')) {
    $('#jj_rubric_dialog').dialog('open');
  }
} catch (e) {
  console.log(e);
}
}

function processDialog() {
// Reset global variable errors
errors = [];
var title, txt, assocMatch, association;
var el = document.getElementById('jj_rubric_title');
if (el.value && el.value.trim() !== '') {
  title = el.value;
  rubricTitle = title;
} else {
  errors.push('You must provide a title for your rubric.');
}
el = document.getElementById('jj_rubric_text');
if (el.value && el.value.trim() !== '') {
  txt = el.value;
} else {
  errors.push('You must paste your rubric into the textbox.');
}
assocMatch = assocRegex.exec(window.location.pathname);
if (assocMatch) {
  var associationType = assocMatch[1].charAt(0).toUpperCase() + assocMatch[1].slice(1);
  association = {
    'type' : associationType,
    'id' : assocMatch[2],
  };
  rubricAssociation = association;
} else {
  errors.push('Unable to determine where to place this rubric.');
}
if (errors.length === 0) {
  criteria = blockRubric(txt) || flexRubric(txt);
  if (typeof criteria === 'object' && criteria.length > 0) {
    checkOutcomes();
  }
}
updateMsgs();
}

function prepareRubric(title, criteria, association) {
if (typeof criteria === 'object' && criteria.length > 0) {
  var formData = addRubric(title, criteria, association);
  if (typeof formData !== 'undefined') {
    saveRubric(formData);
  }
}
}

function saveRubric(formData) {
formData.authenticity_token = getCsrfToken();
var url = window.location.pathname;
$.ajax({
  'cache' : false,
  'url' : url,
  'type' : 'POST',
  'data' : formData,
}).done(function() {
  updateMsgs();
  $('#jj_rubric_dialog').dialog('close');
  window.location.reload(true);
}).fail(function() {
  errors.push('All the information was supplied correctly, but there was an error saving rubric to Canvas.');
  updateMsgs();
});
}

function updateMsgs() {
var msg = document.getElementById('jj_rubric_msg');
if (!msg) {
  return;
}
if (msg.hasChildNodes()) {
  msg.removeChild(msg.childNodes[0]);
}
if (typeof errors === 'undefined' || errors.length === 0) {
  msg.style.display = 'none';
} else {
  var ul = document.createElement('ul');
  var li;
  for (var i = 0; i < errors.length; i++) {
    li = document.createElement('li');
    li.textContent = errors[i];
    ul.appendChild(li);
  }
  msg.appendChild(ul);
  msg.style.display = 'inline-block';
}
}

function blockRubric(txt) {
var criteria = [];
var isValid = true;
var isMethod = false;
try {
  var dequoted = dequote(txt);
  var lines = dequoted.split(/\r?\n/);
  var block = false;
  var newblock;
  var i = 0;
  while (isValid && i < lines.length) {
    var words = lines[i].replace(/[\s\uFEFF\xA0]+$/, '').split(/\t/);
    i++;
    words.map(function(s) {
      return s.trim();
    });
    if (words.length === 1 && words[0] === '') {
      // Ignore blank lines
      continue;
    }
    var outcome = false;
    var name = '';
    var longDesc = '';
    var descriptions = [];
    var points = [];
    if (words.length < 3) {
      // This may be a linked outcome
      if (block && isInteger(words[0])) {
        if (words.length > 1 && isBoolean(words[1], true)) {
          outcome = {
            'id' : words[0],
            'ignore' : getBoolean(words[1]) ? false : true
          };
        } else {
          outcome = {
            'id' : words[0]
          };
          if (words.length > 1) {
            longDesc = words[1];
          }
        }
      } else {
        continue;
      }
    } else {
      newblock = checkPointsRow(words);
      if (newblock !== false) {
        // We have a valid numeric line, start using this from now on.
        block = newblock;
        continue;
      }
    }
    if (block === false) {
      // This is not a row that is all numbers
      if (i > 1) {
        // Must find a points row within the first two rows
        isValid = false;
      }
      continue;
    } else {
      isMethod = true;
    }
    if (!outcome && isValid) {
      if (isInteger(words[0])) {
        if (block.start > 1 && isBoolean(words[1], true)) {
          outcome = {
            'id' : words[0],
            'ignore' : getBoolean(words[1]) ? false : true
          };
        } else {
          outcome = {
            'id' : words[0]
          };
          if (block.start > 1) {
            longDesc = words[1];
          }
        }
      } else {
        name = words[0];
        longDesc = block.start > 1 ? words[1] : '';
      }
      var j = block.start;
      var endAt = words.length < 1 + block.end ? words.length : 1 + block.end;
      var k = 0;
      while (j < endAt) {
        var rating = words[j];
        var point = block.points[k];
        j++;
        k++;
        if (rating !== '') {
          descriptions.push(rating);
          points.push(point);
        }
      }
      if (descriptions.length === 1) {
        errors.push('Only one rating found in line ' + i);
        isValid = false;
      }
      if (isValid && words.length > 1 + block.end) {
        // Check for outcomes
        var extra = [];
        for (var l = 1 + block.end; l < words.length; l++) {
          if (words[l] !== '') {
            extra.push(words[l]);
          }
        }
        if (outcome) {
          // We already have an outcome
          if (typeof outcome.ignore === 'undefined' && isBoolean(extra[0])) {
            outcome.ignore = getBoolean(extra[0]) ? false : true;
          } else {
            errors.push('Invalid content at the end of line ' + i);
            isValid = false;
          }
        } else {
          if (isInteger(extra[0])) {
            if (extra.length > 1 && isBoolean(extra[1])) {
              outcome = {
                'id' : extra[0],
                'ignore' : getBoolean(extra[1]) ? false : true
              };
            } else {
              outcome = {
                'id' : extra[0]
              };
            }
          } else {
            errors.push('Rating without associated points at end of line ' + i);
            isValid = false;
          }
        }
      }
    }
    if (isValid) {
      var item = {
        'name' : name,
        'longDesc' : longDesc,
        'outcome' : outcome,
        'ratings' : descriptions,
        'points' : points
      };
      var criterion = addCriterion(item);
      if (criterion !== false) {
        criteria.push(criterion);
      } else {
        errors.push('Unable to create criterion for line ' + i);
        isValid = false;
      }
    }
  }
} catch (e) {
  console.log(e);
}
return isValid && criteria.length > 0 ? criteria : isMethod;
}

function flexRubric(txt) {
var criteria = [];
var isValid = true;
try {
  var dequoted = dequote(txt);
  var lines = dequoted.split(/\r?\n/);
  var i = 0;
  while (isValid && i < lines.length) {
    var words = lines[i].trim().split(/\t/);
    i++;
    if (words.length === 1 && words[0] === '') {
      // Ignore blank lines
      continue;
    }
    words.map(function(s) {
      return s.trim();
    });
    var outcome = false;
    var name = '';
    var longDesc = '';
    var descriptions = [];
    var points = [];
    var validLine = true;
    var k = 0;
    if (isInteger(words[k])) {
      if (words.length > k + 1 && isBoolean(words[k + 1], true)) {
        outcome = {
          'id' : words[k++],
          'ignore' : getBoolean(words[k++]) ? false : true
        };
      } else {
        outcome = {
          'id' : words[k++]
        };
      }
      while (words.length > k && words[k] === '') {
        k++;
      }
    }
    if (words.length > k) {

      if (outcome && words.length > k + 1 && !isPoints(words[k]) && isPoints(words[k + 1])) {
      } else {
        name = words[k++];
      }
    }
    if (!outcome && words.length > k) {
      if (isInteger(words[k])) {
        // What should be the long description or a rating is an integer
        if (words.length > k + 1 && isBoolean(words[k + 1], true)) {
          outcome = {
            'id' : words[k++],
            'ignore' : getBoolean(words[k++]) ? false : true
          };
        } else {
          outcome = {
            'id' : words[k++]
          };
        }
      }
    }
    if (isValid && words.length > k) {
      if (!isPoints(words[k])) {
        if (words.length == k) {
          longDesc = words[k++];
        } else if (words.length > k + 1 && !isPoints(words[k + 1])) {
          longDesc = words[k++];
        }
      }
    }
    while (isValid && validLine && words.length > k) {
      var description;
      var point;
      if (words.length > k + 1) {
        description = words[k++];
        point = words[k++];
        if (description === '' && point === '') {
          // Skip completely blank pairs
          continue;
        }
        if (!outcome && isInteger(description) && isBoolean(point)) {
          // Have an integer in the rating descriptions
          // Valid if this is the last rating, otherwise invalid
          if (words.length == k) {
            outcome = {
              'id' : description,
              'ignore' : getBoolean(point) ? false : true
            };
          }
        } else {
          if (description === '') {
            validLine = false;
            if (i > 1) {
              errors.push('Empty rating description in line ' + i + ', column ' + (k - 1));
              isValid = false;
            }
          }
          if (!isPoints(point)) {
            validLine = false;
            if (i > 1) {
              errors.push('Second item in pair is not a number in line ' + i + ', column ' + k);
              isValid = false;
            }
          }
          if (isValid && validLine) {
            descriptions.push(description);
            points.push(point);
          }
        }
      } else {
        // Odd number of entries on line, check for outcome
        // or ignore points for outcome
        description = words[k++];
        if (!outcome) {
          if (isInteger(description)) {
            outcome = {
              'id' : description
            };
          } else {
            errors.push('Unbalanced rating/points at the end of line ' + i);
            isValid = false;
          }
        } else {
          if (isBoolean(description)) {
            var thisIgnore = getBoolean(description) ? false : true;
            if (typeof outcome.ignore === 'undefined') {
              outcome.ignore = thisIgnore;
            } else if (outcome.ignore !== thisIgnore) {
              errors.push('Conflicting directives for using outcome for scoring in line ' + i);
              isValid = false;
            }
          }
        }
      }
    }
    if (isValid && validLine) {
      var item = {
        'name' : name,
        'longDesc' : longDesc,
        'outcome' : outcome,
        'ratings' : descriptions,
        'points' : points,
      };
      var criterion = addCriterion(item);
      if (criterion !== false) {
        criteria.push(criterion);
      } else {
        errors.push('Unable to create criterion for line ' + i);
        isValid = false;
      }
    }
  }
} catch (e) {
  console.log(e);
}
return isValid ? criteria : false;
}

function isInteger(t) {
if (typeof t === 'undefined') {
  return false;
}
return /^[0-9]+$/.test(t.trim());
}

function isBoolean(t, req) {
if (typeof t === 'undefined') {
  return false;
}
if (typeof req !== 'undefined' && req && t === '') {
  return false;
}
return /^$|^[01]$/.test(t.trim());
}

function getBoolean(t) {
return (t === false || t === null || t === '' || t === 0 || t === '0') ? false : true;
}

function isPoints(t) {
if (typeof t === 'undefined') {
  return false;
}
return /^([0-9]+|[0-9]+[.][0-9]+|0?[.][0-9]+)$/.test(t);
}

function dequote(txt) {
var regex = new RegExp('([^"]*\\\\n)?["](.*)["](\\\\n[^*"])?$');
var s = txt.replace(/\r?\n/g, '\\n');
s = s.replace(/([^\t]+)/g, quoted);
return s;

function quoted(s) {
  s = s.trim();
  if (regex.test(s)) {
    var match = regex.exec(s);
    if (match) {
      var prefix = typeof match[1] !== 'undefined' ? match[1].replace(/\\n/g, '\n') : '';
      var postfix = typeof match[3] !== 'undefined' ? match[3].replace(/\\n/g, '\n') : '';
      s = prefix + match[2].trim().replace(/""/g, '"') + postfix;
    }
  } else {
    s = s.replace(/\\n/g, '\n');
  }
  return s;
}
}

function checkOutcomes() {
if (criteria === false) {
  return;
}
var i;
var id;
outcomes = [];
pendingOutcomes = 0;
var outcomeIds = [];
// Go through list of outcomes check for duplicates
for (i = 0; i < criteria.length; i++) {
  if (typeof criteria[i].learning_outcome_id !== 'undefined' && isInteger(criteria[i].learning_outcome_id)) {
    id = criteria[i].learning_outcome_id;
    if (outcomeIds.indexOf(id) === -1) {
      outcomes.push({
        'id' : id,
        'loaded' : false
      });
      outcomeIds.push(id);
    }
  }
}
if (outcomes.length > 0) {
  pendingOutcomes = outcomes.length;
  for (i = 0; i < outcomes.length; i++) {
    id = outcomes[i].id;
    var url = '/api/v1/outcomes/' + id;
    $.ajax({
      'url' : url,
      'dataType' : 'json',
      'timeout' : 3000
    }).done(replaceCriteria).fail(checkPendingOutcomes);
  }
} else {
  checkPendingOutcomes();
}
}

function checkPendingOutcomes() {
pendingOutcomes--;
if (pendingOutcomes <= 0) {
  // we're all finished with the fetching of the rubric
  var outstanding = [];
  if (outcomes.length > 0) {
    for (var i = 0; i < outcomes.length; i++) {
      if (outcomes[i].loaded === false) {
        outstanding.push(outcomes[i].id);
      }
    }
  }
  if (outstanding.length > 0) {
    errors.push('Unable to locate outcomes: ' + outstanding.join(', '));
    updateMsgs();
  } else {
    prepareRubric(rubricTitle, criteria, rubricAssociation);
  }
}
}

function replaceCriteria(data) {
if (criteria === false || typeof data === 'undefined') {
  return;
}
for (var i = 0; i < criteria.length; i++) {
  if (criteria[i].learning_outcome_id == data.id) {
    if (criteria[i].description === '') {
      criteria[i].description = data.title;
    }
    if (criteria[i].long_description === '' && typeof data.description !== 'undefined') {
      criteria[i].long_description = data.description;
    }
    if (typeof data.mastery_points !== 'undefined') {
      criteria[i].mastery_points = data.mastery_points;
    }
    if (typeof data.ratings !== 'undefined') {
      criteria[i].ratings = data.ratings;
      criteria[i].points = data.ratings[0].points;
    }
  }
}
for (var j = 0; j < outcomes.length; j++) {
  if (outcomes[j].id == data.id) {
    outcomes[j].loaded = true;
  }
}
checkPendingOutcomes();
}

})();







// --------------------------------------------

// Blackboard Ally
// Removed 05-06-2024

// --------------------------------------------






// Motimatic code

var motc = '2006';
var motu = ENV.current_user_id;
(function() {
    var _mot = window._mot || (window._mot = []);

    if (!_mot.loaded) {
        var motds = document.createElement('script');
        motds.async = true;
        motds.src = '//t.motimatic.com/engine/v2/loadpixels.js';
        var s = document.getElementsByTagName('script')[0];
        s.parentNode.insertBefore(motds, s);
        _mot.loaded = true;
    }
})();
window._mot = window._mot || [];





// --------------------------------------------





//Hide Delete & Conclude Course Buttons in UI

if($.inArray('admin', ENV.current_user_roles) != 1){
    function onElementRendered(selector, cb, _attempts) {
        var el = $(selector);
        _attempts = ++_attempts || 1;
        if (el.length) return cb(el);
        if (_attempts == 60) return;
        setTimeout(function() {
            onElementRendered(selector, cb, _attempts);
        }, 250);
    };

    onElementRendered('.reset_course_content_button', (e) => {
      $("a[href*='confirm_action?event=conclude'").hide();
    });
}

if($.inArray('admin', ENV.current_user_roles) != 1){
    function onElementRendered(selector, cb, _attempts) {
        var el = $(selector);
        _attempts = ++_attempts || 1;
        if (el.length) return cb(el);
        if (_attempts == 60) return;
        setTimeout(function() {
            onElementRendered(selector, cb, _attempts);
        }, 250);
    };

    onElementRendered('.reset_course_content_button', (e) => {
      $("a[href*='confirm_action?event=delete'").hide();
    });
}





// --------------------------------------------





//hide view ungraded as 0 option feb 15 2021
var do_global_customizations = function(){

// Checks if page is course gradebook	
if (/^\/courses\/[0-9]+\/gradebook$/.test(window.location.pathname)) {
    // Removes View Ungraded as 0 menu option
    function HideViewUngradedAs0() {
        $( "li:contains('View Ungraded as 0')" ).css( "display", "none" );
    }
    HideViewUngradedAs0();
    var ViewMenuObserver = new MutationObserver(function(mutations) { 
        mutations.forEach(function(mutation) {
            HideViewUngradedAs0();
        });
    });
    ViewMenuObserver.observe(document.getElementById("gradebook-toolbar"), {
        attributes: true, subtree:true
    }); 
}

};

if (document.readyState === "complete" || (document.readyState !== "loading" && !document.documentElement.doScroll)) {
do_global_customizations();
} else {
document.addEventListener("DOMContentLoaded", do_global_customizations);
}



// --------------------------------------------



// 2021-08-09 prohibit changing full name and sortable name by graying out fields

document.getElementById('user_sortable_name').readOnly = true;
document.getElementById('user_name').readOnly = true;



// --------------------------------------------


// END