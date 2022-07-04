$(document).ready(function() {
    setCookie('tasks', JSON.stringify([]));
    var today = new Date();
    const stemp = today.getFullYear()+'-'+(today.getMonth()+1)+'-'+today.getDate() + ' ' +
     today.getHours() + ":" + today.getMinutes() + ":" + today.getSeconds();
    setCookie('start_date', stemp);
    setCookie('task_count', (0).toString());
    setCookie('task_finish', false);
    var complete_survey_link = survey_link + getCookie('ppid');
    document.getElementById("surveyLink").href = complete_survey_link;
    $("#nextButton").click(function(){
        if(taskTyping){
            taskResponse.response = $('#text_response')[0].value;
            postResponse();
        }
        else{
            if(showTweet){
                taskResponse.response = $("input[name='btnradio2']:checked").val();
                postResponse();
            }
            else{
                taskResponse.response = $("input[name='btnradio']:checked").val();
                postResponse();
            }
        }
        console.log(taskResponse);
        var taskCookie = JSON.parse(getCookie('tasks'));
        taskCookie.push(taskResponse);
        setCookie('tasks', JSON.stringify(taskCookie));
    });
    $("#start").submit(function(event){
        $('#info-section').hide();
        $('#click-here-region').hide();
        $('#task-area').show();
    });

    $("#stop").click(function(){
        clearInterval(intervalID);
        $('#stop-area').hide();
        $('#done-area').show();
        saveResponse();
    });

    $("input[name='btnradio']").change(function(){
        var btnSubmit = document.getElementById("nextButton");
        btnSubmit.disabled = ($(this).val().trim() != "") ? false : true;
    });
    $("input[name='btnradio2']").change(function(e){
        var btnSubmit = document.getElementById("nextButton");
        btnSubmit.disabled = ($(this).val().trim() != "") ? false : true;
    });
});

function EnableDisable(txtPassportNumber) {
    var btnSubmit = document.getElementById("nextButton");
    btnSubmit.disabled = (txtPassportNumber.value.trim() != "") ? false : true;
};

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
    xhr.open('POST', task2Server, true);
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

function postResponse(response){
    if(taskTyping){
        $('#text_response')[0].value = '';
        EnableDisable($('#text_response')[0]);
    }
    else{
        $('input[name="btnradio"]').prop('checked', false);
        $('input[name="btnradio2"]').prop('checked', false);
        $('input[id="nextButton"]').prop('disabled', true);
    }
    update_values();
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
