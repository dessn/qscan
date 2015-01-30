/******************************************
qscan jQuery

* defines infinite scroll behavior for
  the qscan main page
* defines AJAX call to log scanning 
  decisions

by danny goldstein 2014
******************************************/

jQuery(document).ready(function() {

    //on scroll gets when bottom of the page is reached and calls th
    //function do load more content

	$(window).data('ajaxready', true).scroll(function(e){

	//Not always the pos == h statement is verified, expecially on
	//mobile devices, that's why a 300px of margin are assumed.

	if($(window).scrollTop() + $(window).height() >= 
	   $(document).height() - 300) {
	    console.log("bottom of the page reached!");
	    $('#loader').fadeIn('slow', function() {
		    $.get($SCRIPT_ROOT + '/fetch_more', function(data){
			    $('#loader').fadeOut('slow', function(){
				    $('#append-target').append(data).fadeIn(999);
				});
			});
		});
	 G   
	}
	    });   
	
	// Log scanning decisions. 
    
    $(".scanobj-container").click(function() {
	    $.post($SCRIPT_ROOT + '/register_scan',
		   {snobjid: int($(this).children('.panel-info')
				 .first().text())}
		   function(data){
		       if (data.result){
			   $(this).toggleClass("clicked");
		       }		       
		   });
	});
    });
