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

        function imgErrorHandler() {
          var rents = $(this).parents('.object-frame');
          var $this = $(this);
          if (!rents.hasClass('panel-warning')){
              rents.removeClass('panel-default panel-success').addClass('panel-warning');
              rents.attr('style', 'cursor:default');
              var h3 = rents.find('h3').first();
              h3.append('<div class="pull-right">Missing Images <span class="glyphicon glyphicon-question-sign" aria-hidden="true"></span></div>').fadeIn(999);
          }
          $.get($SCRIPT_ROOT + '/missing',
                    function(link){
                      $this.attr('src', link); 
                    });
        }


	// When there are no objects left on the server, cease all AJAX
	// calls to fetch new objects by toggling the fetchobjects
	// variable.
        

        function submit_callback(){
            var numsaved = $('.object-frame.panel-success').length;
            var numignored = $('.object-frame.panel-default').length;
            var nummissing = $('.object-frame.panel-warning').length;
            $('#loadmore-btn').prop('disabled', true);
            $.post($SCRIPT_ROOT + '/render_done',
                   {numsaved:numsaved,
                           numignored:numignored,
                           nummissing:nummissing},
                   function(html){
                       $('#scroll-container').append(html).fadeIn('slow');
                       $('#submit-btn').prop('disabled',true);
                       $('#submitbadge').remove();
                       $('html, body').animate({ scrollTop: $(document).height()}, "slow");
                   });            
        }        
        
        function get_snobjids(el){
            var arr = el.find('h3').clone().children().remove().end();
            var ids = (function() {
                          var _i, _len, _results;
                          _results = [];
                          for (_i = 0, _len = arr.length; _i < _len; _i++) {
                          snobjid = arr[_i].textContent;
                          _results.push(snobjid);
                          }
                          return _results;
                      })();
            return ids;
        }  

        function placeButtons(){
            $.get($SCRIPT_ROOT + '/buttons',
                  function(html){
                      $('#button-container').append(html)
                          .fadeIn(999, function(){
                                          $('#submitbadge').text($('.object-frame').length);
                                        });
                      $('#submit-btn').click(function(){
                              $.post($SCRIPT_ROOT + '/submit',
                                     {save:get_snobjids($('.object-frame.panel-success')),
                                      junk:get_snobjids($('.object-frame.panel-default')),
                                      missing:get_snobjids($('.object-frame.panel-warning'))},
                                     submit_callback
                                     );
                          });
                      $('#loadmore-btn').click(function(){
                              $('#loader').fadeIn('slow', function(){
                                                                var exclude = get_snobjids($('.object-frame'));
                                                                fetchScanObjectsAjax(exclude);
                                                          });
                              $('#loader').fadeOut('slow');
                          });
                  });
        }
        
	function fetchScanObjectsAjax(exclude){
            $('img').removeClass('new');
	    $.post($SCRIPT_ROOT + '/fetch_more',
                   {exclude:exclude},
                   function(json){
                       var done      = json.has_data;
                       var html      = json.html;
                       var numnew    = json.numnew;
                       
                       $('#scroll-container').append(html)
                           .fadeIn(999,
                             function(){
                                $("img.new").on("error", imgErrorHandler);
                                $('#submitbadge').text($('.object-frame').length);
                                if (done){
                                   $('#loadmore-btn').prop('disabled', true);
                                }
                                });
                       
                   });
	}
	


	// Set up the page with an initial fetch.
  
	fetchScanObjectsAjax([]);

        // Also add the buttons.
        
        placeButtons();

	// When someone clicks a panel, turn it on / off in the browser
	// and on the backend.
 
	$('#scroll-container').on("click", ".object-frame", function(e){
             if (!$(this).hasClass('panel-warning')){
		var h3 = $(this).find('h3').first();
		var snobjid = h3.clone().children().remove().end().text();
		console.log('clicked on ' + snobjid);
		var is_saved = $(this).hasClass('panel-success');
		
                if (is_saved){
                        h3.find('.pull-right').remove().fadeOut(999);
                } else {
		        h3.append('<div class="pull-right">Saved <span class="glyphicon glyphicon-ok-circle" aria-hidden="true"></span></div>').fadeIn(999);
                }
                $(this).toggleClass('panel-default');
                $(this).toggleClass('panel-success');
              }
	    });
    });