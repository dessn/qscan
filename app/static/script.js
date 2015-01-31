/******************************************
qscan jQuery

* defines infinite scroll behavior for
  the qscan main page
* defines AJAX call to log scanning 
  decisions

by danny goldstein 2014
******************************************/

jQuery(document).ready(function() {

    // When you hit bottom, load more crap to scan.
  
    $(window).data('ajaxready', true).scroll(function(e){
	if ($(window).data('ajaxready') === false) return;
	
	if ($(window).scrollTop() + $(window).height() >= 
            $(document).height() - 300) {
	    console.log("bottom of the page reached!");
	    
	    // See if there is anything left to fetch.
	    
	    var anything_left = $.getJSON($SCRIPT_ROOT + '/anything_left',
					  function(data){
					      return data.answer
                                      });
	    
	    if (anything_left){	    
		$('#loader').fadeIn('slow', function() {
		    $(window).data('ajaxready', false);
		    $.get($SCRIPT_ROOT + '/fetch_more', function(data){
			$('#loader').fadeOut('slow', function(){
			    $('#append-target').append(data).fadeIn(999);
			});
		    });
		});
	    }
	}
    });   
    
    // Log scanning decisions. 
    
    $(".panel").click(function() {
	$.post($SCRIPT_ROOT + '/register_scan',
	       {snobjid: int($(this).find('.panel-title')
			     .first().text())}
	       function(data){
		   var response = jQuery.parseJSON(data);
		   if (response.flip){
		       $(this).toggleClass("focus");
		   }		       
	       });
    });
});
