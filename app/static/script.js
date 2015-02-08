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
        

        function submit_callback(){
            var numsaved = $('.object-frame.panel-success').length;
            var numignored = $('.object-frame.panel-default').length;
            $('#loadmore-btn').prop('disabled', true);
            $.post($SCRIPT_ROOT + '/render_done',
                   {numsaved:numsaved,
                           numignored:numignored},
                   function(html){
                       $('#scroll-container').append(html).fadeIn('slow');
                       #('#submit-btn').prop('disabled',true);
                       $('html, body').animate({ scrollTop: $(document).height()}, "slow");
                   });            
        }        
        
        functon get_snobjids(el){
            el.find('h3').each(function(){
                    return $(this).clone().children().remove().end().text();
                });
        }

        function placeButtons(){
            $.get($SCRIPT_ROOT + '/buttons.html',
                  function(html){
                      $('#button-container').append(html)
                          .fadeIn(999);
                      $('#submit-btn').click(function(){
                              $.post($SCRIPT_ROOT + '/submit',
                                     {save:get_snobjids($('.object-frame.panel-success')),
                                             junk:get_snobjids($('.object-frame.panel-default'))},
                                     submit_callback
                                     );
                          });
                      $('#loadmore-btn').click(function(){
                              $('#loader').fadeIn('slow', function(){
                                      fetchScanObjectsAjax();
                                  });
                              $('#loader').fadeOut('slow');
                          });
                  });
        }
        
	function fetchScanObjectsAjax(){
	    $.getJSON($SCRIPT_ROOT + '/fetch_more',
		      function(json){
			  fetchobjects  = json.has_data;
			  var html      = json.html;
			  var numnew    = json.numnew;
                          
			  $('#scroll-container').append(html)
			      .fadeIn(999);
                      });
	}
	


	// Set up the page with an initial fetch.
  
	fetchScanObjectsAjax();

        // Also add the buttons.
        
        placeButtons();

	// When someone clicks a panel, turn it on / off in the browser
	// and on the backend.
 
	$('#scroll-container').on("click", ".object-frame", function(e){
    
		var h3 = $(this).find('h3').first();
		var snobjid = h3.clone().children().remove().end().text();
		console.log('clicked on ' + snobjid);
		var is_saved = $(this).hasClass('panel-success');
		var $this = $(this);
    
		console.log('starting post request for ' + snobjid);
		$.post($SCRIPT_ROOT + '/set_object_label',
		       {snobjid:snobjid,
			       action:'click'},
		       function(){ 
			   if (is_saved){
			       h3.find('.pull-right').remove().fadeOut(999);
			   } else {
			       h3.append('<div class="pull-right">Saved <span class="glyphicon glyphicon-ok-circle" aria-hidden="true"></span></div>').fadeIn(999);
			   }
       
			   $this.toggleClass('panel-default');
			   $this.toggleClass('panel-success');
	
		       });
	    });
    });