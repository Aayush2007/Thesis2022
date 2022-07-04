$(document).ready(function() {
    console.log('$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$$')
    setCookie('tasks', JSON.stringify([]));
    setCookie('sentence', JSON.stringify([]));
    sessionStorage.setItem('s_keypoints', JSON.stringify([]));
    var today = new Date();
    const stemp = today.getFullYear()+'-'+(today.getMonth()+1)+'-'+today.getDate() + ' ' +
     today.getHours() + ":" + today.getMinutes() + ":" + today.getSeconds();
    setCookie('start_date', stemp);
    setCookie('try_task_count', (0).toString());
    setCookie('task_count', (0).toString());
    setCookie('task_finish', false);
    setCookie('task_limit', (0).toString());
    //setCookie('show_button', true);

    if (document.getElementById("surveyLink") != null){
        var complete_survey_link = survey_link + getCookie('ppid');
        document.getElementById("surveyLink").href = complete_survey_link;
    }

    if (getCookie('try_mode') == "true"){
        //setCookie('show_button', false);
        setCookie('task_limit', tryTasks);
        setItems();
        startTimer();
        tryInterval = setInterval(function(){
                            setItems();
                            startTimer();
                        }, 16000);
    }
    else if (getCookie('start_mode') == "true"){
        //setCookie('show_button', false);
        setCookie('task_limit', totalTasks);
        setItems();
        startTimer();
        tryInterval = setInterval(function(){
                            setItems();
                            startTimer();
                        }, 16000);
    }

    $('#try').click(function(){
        postTryHome();
        $('#click-here-region').hide();
    });

    $("#start").submit(function(event){
        $('#info-section').hide();
        $('#click-here-region').hide();
        $('#task-area').show();
    });

    $("#stop").click(function(){
        //clearInterval(intervalID);
        $('#stop-area').hide();
        $('#done-area').show();
        saveResponse();
    });
});

function saveResponse(){

    var today = new Date();
    const etemp = today.getFullYear()+'-'+(today.getMonth()+1)+'-'+today.getDate() + ' '
     + today.getHours() + ":" + today.getMinutes() + ":" + today.getSeconds();

    resObj = {
        'start_date': getCookie('start_date'),
        'prolific_pid': getCookie('ppid'),
        'session_id': getCookie('sid'),
        'tasks': JSON.parse(getCookie('tasks')),
        'end_date': etemp
    };

    let formdata = new FormData();
    formdata.append("response", JSON.stringify(resObj));
    let xhr = new XMLHttpRequest();
    xhr.open('POST', taskServer, true);
    xhr.onload = function () {
        if (this.status === 200) {
            console.log("DONE.");
        }
        else {
            console.error(xhr);
        }
    };
    xhr.send(formdata);
}

function setItems(){
    //console.log("In setItems....................................")

    if ((getCookie('start_mode') == "true") && (parseInt(getCookie('task_count')) != 0)){
        taskResponse = {
                    'image_name': questionImage,
                    'question': questionToAsk,
                    'tweet': encodeURIComponent(tweetToShow),
                    'label': taskLabel,
                    'response': JSON.parse(getCookie('sentence'))
                  };

        var taskCookie = JSON.parse(getCookie('tasks'));
        taskCookie.push(taskResponse);
        setCookie('tasks', JSON.stringify(taskCookie));
    }


    if (getCookie('try_mode') == "true"){
        setCookie('try_task_count', (parseInt(getCookie('try_task_count')) + 1).toString());
    }
    else if (getCookie('start_mode') == "true"){
        setCookie('task_count', (parseInt(getCookie('task_count')) + 1).toString());
    }

    sessionStorage.setItem('s_keypoints', JSON.stringify([]));

    let formdata = new FormData();
    //formdata.append("sentence", JSON.parse(getCookie('sentence')));

    let xhr = new XMLHttpRequest();
    xhr.open('POST', setItemServer, true);
    xhr.onload = function () {
        if (this.status === 200) {
            console.log(this.response);
            var items = JSON.parse(this.response).items;
            questionToAsk = items.question;
            questionImage = items.image_name;
            tweetToShow = items.tweet;
            taskLabel = items.label;
            setCookie('sentence', JSON.stringify([]));
            $('#pResponse').text([]);
            update_values();
        }
        else {
            console.error(xhr);
        }
    };
    xhr.send(formdata);
}

function postTryHome(){
    setCookie('try_mode', true);
    let formdata = new FormData();
    formdata.append("tryMode", true);

    let xhr = new XMLHttpRequest();
    xhr.open('POST', tryModeServer, true);
    xhr.onload = function () {
        if (this.status === 200) {
            $('#trySend').click();
        }
        else {
            console.error(xhr);
        }
    };
    xhr.send(formdata);
}

//Add file blob to a form and post
function postFile(frameInfo, lh, rh) {

    //Set options as form data
    let formdata = new FormData();
    formdata.append("image", JSON.stringify(frameInfo));
    formdata.append("lh", JSON.stringify(lh));
    formdata.append("rh", JSON.stringify(rh));

    let xhr = new XMLHttpRequest();
    xhr.open('POST', apiServer, true);
    xhr.onload = function () {
        if (this.status === 200 && JSON.parse(this.response).success) {
            setCookie('sentence', JSON.stringify(JSON.parse(this.response).result));
            $('#pResponse').text(JSON.parse(this.response).result);
        }
        else {
            //console.error(xhr);
        }
    };
    xhr.send(formdata);
}

function startTimer() {
    time1 = 1;
    clearInterval(timerInterval);
  timerInterval = setInterval(function() {
    if (time1 <= 15) {
      document.getElementById("timeKeep").innerHTML = time1;
      time1 += 1
    } else if (time1 > 15) {

    }
  }, 1000);
}

function setCookie(cname, cvalue, exdays) {
  const d = new Date();
  d.setTime(d.getTime() + (exdays*24*60*60*1000));
  let expires = "expires="+ d.toUTCString();
  document.cookie = cname + "=" + cvalue + ";" + expires + ";path=/";
}

function getCookie(cname) {
  let name = cname + "=";
  let ca = document.cookie.split(';');
  for(let i = 0; i < ca.length; i++) {
    let c = ca[i];
    while (c.charAt(0) == ' ') {
      c = c.substring(1);
    }
    if (c.indexOf(name) == 0) {
      return c.substring(name.length, c.length);
    }
  }
  return "";
}