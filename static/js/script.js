

function showUncertaintiesbox() {
    var checkBox = document.getElementById("uncert_checkbox");
    var text = document.getElementById("incertezze");
    if (checkBox.checked == true){
      text.style.display = "block";
    } else {
       text.style.display = "none";
    }
  }

  