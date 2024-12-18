$.getCurrentDate = function() {
    var nowDate = new Date();

    hour = nowDate.getHours()
    day = nowDate.getDate()
    month = nowDate.getMonth() + 1
    year = nowDate.getFullYear()

    day = day + 1
    if ((day > 31 && (month == 1 || month == 3 || month == 5 || month == 7 || month == 8 || month == 10 || month == 12)) || 
        (day > 28 && month == 2) || 
        (day > 30 && (month == 4 || month == 6 || month == 9 || month == 11))) {
        day = 1
        month = month + 1
    }

    if (month > 12) {
        month = 1
        year = year + 1
    }

    return year + "-" + month + "-" + day;
}

$.getStartDate = function(currentDate, wantedShowDays) {
    var d = currentDate.split("-");
    var year = parseInt(d[0])
    var month = parseInt(d[1])
    var day = parseInt(d[2])
    
    var tM = month
    var tY = year
    var lastMonth = month - 1
    if (lastMonth < 1) {
        lastMonth = 12
    }

    var tD = day - wantedShowDays

    if (tD < 1) {
        if (lastMonth == 1 || lastMonth == 3 || lastMonth == 5 || lastMonth == 7 || lastMonth == 8 || lastMonth == 10 || lastMonth == 12) {
            tD = 31 + tD
        } else if (lastMonth == 2) {
            tD = 28 + tD
        } else {
            tD = 30 + tD
        }

        tM = month - 1

        if (month == 1) {
            tM = 12
            tY = year - 1
        }
    }

    return tY + "-" + tM + "-" + tD
}

$.urlParam = function(name) {
    var results = new RegExp('[\?&]' + name + '=([^&#]*)').exec(window.location.href);
    if (results == null) {
        return ""
    }
    return results[1] || 0;
}


$.formatDate = function(d) {
    if (d < 10) {
        return "0" + d
    }

    return d
}

$.convertDateString = function(datetime) {
        var offset = datetime.getTimezoneOffset()

        //hour = datetime.getHours() + (offset / 60)
        hour = datetime.getHours()
        day = datetime.getDate()
        month = datetime.getMonth() + 1
        year = datetime.getFullYear() % 2000 
        if (hour >= 24) {
            hour = 0
            day = day + 1
        }

        if (day > 31 && (month == 1 || month == 3 || month == 5 || month == 7 || month == 8 || month == 10 || month == 12)) {
            day = 1
            month = month + 1
        } else if (day > 30 && (month == 4 || month == 6 || month == 9 || month == 11)) { 
            day = 1
            month = month + 1
        } else if (day > 28 && month == 2) {
            day = 1
            month = month + 1
        }

        if (month > 12) {
            year = year + 1
        }

        dformat = $.formatDate(month) + "/" + $.formatDate(day) + "/" + $.formatDate(year) + " "
        dformat = dformat + $.formatDate(hour) + ":" + $.formatDate(datetime.getMinutes()) + ":" + $.formatDate(datetime.getSeconds())

        return dformat
 }

$.checkFieldEmpty = function(field) {
    if (field == null || field == "") {
        return "-"
    }

    return field
}
