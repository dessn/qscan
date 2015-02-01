/************************
qscan jQuery

* infinite scroll for
  the qscan main page

* AJAX to log scanning 
  decisions

by danny goldstein 2014
*************************/

jQuery(document).ready(function() {

    // Always start from the top.

    $(window).on('beforeunload', function() {
	    $(window).scrollTop(0);
    });
   
    // When there are no objects left on the server, cease all AJAX
    // calls to fetch new objects by toggling the fetchobjects
    // variable.

    var fetchobjects = true;

    // Set up the page with an initial fetch.
    
    fetchScanObjectsAjax();

    // When you hit the bottom of the page, load more crap to scan.
    // The 'ajaxready' variable prevents multiple AJAX calls from
    // being launched from a single bottom-hit.

    $(window).data('ajaxready', true);
    $(window).scroll(function(e){
	    if (!$(window).data('ajaxready') || !fetchobjects) return;
	    if ($(window).scrollTop() + $(window).height() >= $(document).height() - 300){
		console.log("Reached the bottom of the page!");
		$(window).data('ajaxready', false);
		$('#loader').fadeIn('slow', function(){
			fetchScanObjectsAjax();
		    });
		$('#loader').fadeOut('slow', function(){
			$(window).data('ajaxready', true);
		    });
	    }
	});
    
    // When someone clicks a panel, turn it on / off in the browser
    // and on the backend.
    
    $('#scroll-container').on("click", ".panel-default", function(e){
	    var snobjid = $(this).find('.panel-title').first().text();	
	    var $this = $(this);
	    console.log(snobjid);
	    $.post($SCRIPT_ROOT + '/register_scan',
		   {snobjid:snobjid},
		   function(response){
		       console.log('response is ' + response.flip);
		       if (response.flip){
		   	   $this.toggleClass("focus");
		       }
		   },
		   'json');
	});
    
    function fetchScanObjectsAjax(){
	$.getJSON($SCRIPT_ROOT + '/fetch_more',
		  function(json){
		      fetchobjects  = json.has_data;
		      var html      = json.html;
		      $('#scroll-container').append(html).fadeIn(999);
		  });
    }
    
    });
