/** 
    @Author:    Nicholas Bannister-Andrews
    @Date:      Saturday, January 7th, 2012
    
*/

(function(webapp, $, undefined) {
    
     /** ==============================================
        PUBLIC FUNCTIONS
     ------------------------------------------------- */
    webapp.getProjects = function(format) {
        console.log(format);
        if (format === "json") {
            getProjects_json();
        }
    };
    
    
    /** ==============================================
        PRIVATE FUNCTIONS
     ------------------------------------------------- */
     
    /** ----------------------------------------------
       function getProjects_json:
       @ Uses jsonp to get the list of projects.
      ---------------------------------------------- */
    function getProjects_json() {
        console.log("getProjects_json");
        $.jsonp({
            url: "http://localhost:8083/api/v1/ajax/view/projects/list?f=json&c=10&callback=?",
            success: function(json, status) {
                // null/undefined checks are in the function now.
                $('#projects_list').append(processProjects_json(json));
            },
            error: function(options, status) {
                getProjects_error("Error. 1");
            }
        });
    };
    
    
    /**----------------------------------------------------
        function processProjects_json(json):
        @Parameter: json
        json data returned from the API call. 
     ---------------------------------------------------- */
    function processProjects_json(json) {
        var projectsList = '', projectsListItem = '', projectsListItemData = '';
        var jsonProjects, project;
        if (!webapp.utils.isNullOrUndefined(json) && !webapp.utils.isNullOrUndefined(json.projects)) {
            console.log("NOT NULL OR UNDEFINED");
            jsonProjects = json.projects;
            for (project = 0; project < jsonProjects.length; project++) {
                projectsListItem = ''; // clear
                projectsListItemData = ''; // clear
                projectsListItemData = projectsListItemData+'<div class="title">' + jsonProjects[project].title + '</div>';
                projectsListItemData = projectsListItemData+'<div class="url">' + jsonProjects[project].url + '</div>';
                projectsListItemData = projectsListItemData+'<div class="description">' + jsonProjects[project].description + '</div>';
                projectsListItem = '<li>' + projectsListItemData + "</li>";
                projectsList += projectsListItem;
            }
            projectsList = '<ul id="project_list">' + projectsList + "</ul>";
            return projectsList;
        } else {
            return getProjects_error("No projects.");
        }
    };
    
    function getProjects_error(errorString) {
        console.log("getProjects_error");
        if ( !webapp.utils.isNullOrUndefined(errorString) ) {
            if (errorString !== '') {
                return errorString;
            } else {
                return ''; // msg is empty so return a real string.
            }
        } else {
            return ''; //    
        }
    };
    
    
}(window.webapp = window.webapp || {}, jQuery));





(function(utils, $, undefined) {
    console.group('aquaspy.utils');
    
    
    /* ------------------------------------------------------
        utils.isNullOrUndefined(thing):
        @Parameter: thing - an object or value to test.
        
        @Returns: true if the typeof thing is "null" or 
        "undefined"; false otherwise.
     * ---------------------------------------------------- */
    utils.isNullOrUndefined = function(thing) {
        if (utils.isNull(thing) || utils.isUndefined(thing)) {
            return true;
        }
        return false;
    };
    
    
    
    
    /* ------------------------------------------------------
        utils.isNull(thing):
        @Parameter: thing - an object or value to test.
        
        @Returns: true if the typeof the thing is "null";
        false otherwise.
     * ---------------------------------------------------- */
    utils.isNull = function(thing) {
        if (thing === null) {
            return true;
        }
        return false;
    };
    
    
    
    
    /* ------------------------------------------------------
        utils.isUndefined(thing):
        @Parameter: thing - an object or value to test.
        
        @Returns: true if the typeof the thing is "undefined";
        false otherwise.
     * ---------------------------------------------------- */
    utils.isUndefined = function(thing) {
        if (typeof thing === "undefined") {
            return true;
        }
        return false;
    };
    
    
    
    
    /** ------------------------------------------------------
        utils.doesElementExist(selector):
        @Parameter: selector - a CSS selector (string or 
        jQuery obj) to test for.
        
        @Returns: True iff there is one or more element named 
        by the given selector (could already be a jQery Object);
        False in all other cases;
      */
    utils.doesElementExist = function(selector) {
        var jQObj;
        if (aquaspy.utils.isNullOrUndefined(selector)) {
            return false;
        } else if (typeof selector === "number") {
            return false;
        } else { // something else.
            jQObj = $(selector);
            if (aquaspy.utils.isNullOrUndefined(jQObj)) {
                return false;
            } else if (parseInt(jQObj.length, 10) === 0) {
                return false;
            } else if (parseInt(jQObj.length, 10) > 0) {
                return true;
            }
        }
        return false;
    };
    
    
    
    
    /** ----------------------------------------------------
     utils.trimString(string):
     @Parameter: string - a string to trim
     @Returns: the string with all whitespace from beginning
     and end of the string removed. Whitespace between the 
     first and last non-whitespace characters is unaffected.
      ---------------------------------------------------- */
    utils.trimString = function (string) {
        
    };
    console.groupEnd();
}(window.webapp.utils = window.webapp.utils || {}, jQuery));

(function() {
    // Add a method conditionally.
    /** -------------------------------------------------------
        Function.prototype.method(name, func)
        Add a method conditionally.
     ------------------------------------------------------- */
    Function.prototype.method = function (name, func) { 
        if (!this.prototype[name]) {
            this.prototype[name] = func;
        }
    };
    
    /** -------------------------------------------------------
        String.trim method
        Trims whitespace from *both* front and back of string.
     ------------------------------------------------------- */
    String.method('trim', function () { 
        return this.replace(/^\s+|\s+$/g, '');
    });
    
    /** -------------------------------------------------------
        String.trimBack
        Trims whitespace from just the back of the string.
     ------------------------------------------------------- */
    String.method('trimBack', function () { 
        return this.replace(/\s+$/g, '');
    });
    
    /** -------------------------------------------------------
        String.trimFront
        Trims whitespace from just the front of the string.
     ------------------------------------------------------- */
    String.method('trimFront', function () { 
        return this.replace(/^\s+/g, '');
    });
    
}());