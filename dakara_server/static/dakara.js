function getCookie(name) {
    var cookieValue = null;
    if (document.cookie && document.cookie != '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = jQuery.trim(cookies[i]);
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, name.length + 1) == (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}

var csrftoken = getCookie('csrftoken');

function csrfSafeMethod(method) {
    // these HTTP methods do not require CSRF protection
    return (/^(GET|HEAD|OPTIONS|TRACE)$/.test(method));
}

$.ajaxSetup({
    beforeSend: function(xhr, settings) {
        if (!csrfSafeMethod(settings.type) && !this.crossDomain) {
            xhr.setRequestHeader("X-CSRFToken", csrftoken);
        }
    }
});

$.notify.addStyle('dakara', {
  html: "<div><span data-notify-text/></div>",
  classes: {
    base: {
      "white-space": "nowrap",
      "padding": "5px",
      "color": "#191919",
      "background": "#19FFB0"
    }
  }
});


var previousTiming;

var LibraryEntry = React.createClass({
    handleAdd: function() {
        var songId = this.props.song.id;
        this.props.addToPlaylist(songId);
    },
    render: function() {
        return (
                <li>
                    <div className="data">
                        {this.props.song.title}
                    </div>
                    <div className="controls" id={"song-" + this.props.song.id}>
                        <div className="add control-primary" onClick={this.handleAdd}>
                            <i className="fa fa-play"></i>
                        </div>
                    </div>
                </li>
        );
    }
});

var Library = React.createClass({
    getInitialState: function() {
        return {libraryEntries: {count: 0, results: []}, search: ""};
    },

    componentDidMount: function() {
        this.refreshEntries(this.props.url + "library/songs/");
    },

    handleNext: function() {
        this.refreshEntries(this.state.libraryEntries.next);
    },

    handlePrevious: function() {
        this.refreshEntries(this.state.libraryEntries.previous);
    },

    handleFirst: function() {
        if (this.state.libraryEntries.previous) {
            this.refreshEntries(this.props.url + "library/songs/?title=" + encodeURIComponent(this.state.search));
        }
    },

    handleLast: function() {
        if (this.state.libraryEntries.next) {
            this.refreshEntries(this.props.url + "library/songs/?page=last&title=" + encodeURIComponent(this.state.search));
        }
    },

    handleSearchChange: function(e) {
        this.setState({search: e.target.value});
    },

    handleSubmit: function(e) {
        e.preventDefault();
        this.handleSearch(e);
    },

    handleSearch: function(e) {
        this.refreshEntries(this.props.url + "library/songs/?title=" + encodeURIComponent(this.state.search));                
    },

    addToPlaylist: function(songId) {
        $.ajax({
        url: this.props.url + "playlist/",
        dataType: 'json',
        type: 'POST',
        data: {"song": songId},
        success: function(data) {
            $("#song-" + songId).notify("Added to Playlist", {style: "dakara", position: "left"});
            this.props.loadStatusFromServer();
        }.bind(this),
        error: function(xhr, status, err) {
        console.error(this.props.url, status, err.toString() + xhr.responseText);
        }.bind(this)
        }); 
    },

    refreshEntries: function(url) {
        if (url) {
            $.ajax({
              url: url,
              dataType: 'json',
              cache: false,
              success: function(data) {
                this.setState({libraryEntries: data});
              }.bind(this),
              error: function(xhr, status, err) {
                console.error(this.props.url, status, err.toString());
              }.bind(this)
            });
        }
    },

    render: function() {
        var addToPlaylist = this.addToPlaylist;
        var list = this.state.libraryEntries.results.map(function(entry){
            return (<LibraryEntry song={entry} addToPlaylist={addToPlaylist}/>);
        });
        var count = this.state.libraryEntries.count;
        var hasNext = this.state.libraryEntries.next;
        var hasPrevious = this.state.libraryEntries.previous;
        return (
        <div>
            <form id="query" onSubmit={this.handleSubmit}>
                <div className="field">
                    <input type="text" value={this.state.search} onChange={this.handleSearchChange}/>
                </div>
                <div className="controls">
                    <div className="search control-primary" onClick={this.handleSearch}>
                        <i className="fa fa-search"></i>
                    </div>
                </div>
            </form>
            <div id="results">
                <ul id="results-listing" className="listing">
                    {list}
                </ul>
            </div>
            <nav id="paginator">
                <div className="controls">
                    <div className={"first control-primary" + (hasPrevious? "" : " disabled")} onClick={this.handleFirst}>
                        <i className="fa fa-angle-double-left"></i>
                    </div>
                    <div className={"previous control-primary" + (hasPrevious? "" : " disabled")} onClick={this.handlePrevious}>
                        <i className="fa fa-angle-left"></i>
                    </div>
                    <div className={"next control-primary" + (hasNext? "" : " disabled")} onClick={this.handleNext}>
                        <i className="fa fa-angle-right"></i>
                    </div>
                    <div className={"last control-primary" + (hasNext? "" : " disabled")} onClick={this.handleLast}>
                        <i className="fa fa-angle-double-right"></i>
                    </div>
                </div>
                <div className="info">
                    <div classname="info-item" id="library-amount">
                        <span className="stat">{count}</span>
                        <span className="description">song{count == 1? '': 's'} found</span>
                    </div>
                </div>
            </nav>
        </div>
        );
    }
});




var Player = React.createClass({
    getInitialState: function() {
        return {pauseCmd: null, skip: -1};
    },

    handlePlayPause: function(e){
        if (this.props.playerStatus.playlist_entry){
            var pause = !this.props.playerStatus.paused;
            this.setState({pauseCmd: pause});
            this.props.sendPlayerCommand({"pause": pause});
        }
    },

    handleSkip: function(e){
        if (this.props.playerStatus.playlist_entry){
            this.props.sendPlayerCommand({"skip": true});
            this.setState({pauseCmd: null, skip: this.props.playerStatus.playlist_entry.id});
        }
    },

    render: function() {
        var playerStatus = this.props.playerStatus;
        var timing = playerStatus.timing;
        if (timing){
            timing = timing.substring(3,8);
            previousTiming = timing;
        } else {
            timing = previousTiming;
            console.error("timing null");
        }
        var songName;
        var playIcon = "fa fa-";
        var playingId;
        if (playerStatus.playlist_entry){
            songName = playerStatus.playlist_entry.song.title;
            playingId = playerStatus.playlist_entry.id;
            playIcon += playerStatus.paused ? "play" : "pause";
        } else {
            playIcon += "stop";
        }

        var waitingPause = false;
        if (this.state.pauseCmd != null) {
            waitingPause = (this.state.pauseCmd != playerStatus.paused);
        }
        var waitingSkip = (this.state.skip == playingId);

        var playPausebtn;
        if (waitingPause) {
            playPausebtn = <img src="/static/pending.gif"/>
        } else {
            playPausebtn = <i className={playIcon}></i>
        }

        var skipBtn;
        if (waitingSkip) {
            skipBtn = <img src="/static/pending.gif"/>
        } else {
            skipBtn = <i className="fa fa-step-forward"></i>
        }

        return (
        <div id="player">
            <div className="controls">
                <div className={"play-pause control-primary" + (playerStatus.playlist_entry && !waitingPause ? "" : " disabled")} onClick={this.handlePlayPause}>
                    {playPausebtn} 
                </div>
                <div className={"skip control-primary" + (playerStatus.playlist_entry && !waitingSkip ? "" : " disabled")} onClick={this.handleSkip}>
                    {skipBtn}
                </div>
            </div>
            <div id="playlist-current-song" className="details">
                <span className="title">{songName}</span>
            </div>
            <div className="status">
                <span id="playlist-current-timing" className="current">{timing}</span>
            </div>
        </div>
        );

    }
});

var PlaylistEntry = React.createClass({
    handleRemove: function(e){
            this.props.removeEntry(this.props.entry.id);
    },

    render: function(){
        return (
            <li>
                <div className="data">
                    {this.props.entry.song.title} 
                </div>
                <div className="controls">
                    <div className="remove control-danger" onClick={this.handleRemove}>
                        <i className="fa fa-times"></i>
                    </div>
                </div>
            </li>
        );
    }
});


var Playlist = React.createClass({
    handleCollapse: function() {
        this.setState({collapsed: !this.state.collapsed});
    },
    getInitialState: function() {
        return {collapsed: true};
    },

    render: function() {
        var playingId = this.props.playingId; 
        var list = this.props.entries.results;
        var playingIndex = list.map(function(item) { return item.id; })
               .indexOf(playingId);
        //remove current playing id from list
        if (playingIndex > -1){
            list.splice(playingIndex,1);
        } 
        var playlistEntries;
        var next;
        if (!this.state.collapsed){
            var removeEntry = this.props.removeEntry;
            playlistEntries = list.map(function(entry) {
                return ( <PlaylistEntry entry={entry} removeEntry={removeEntry}/> );
            });
        } else {
            if (list[0]){
                next = (
                    <div className="info-item" id="playlist-info-next">
                        <span className="stat">Next</span>
                        <span className="description">{list[0].song.title}</span>
                    </div>
                );
            }
        }
        
        var playlistSize = this.props.entries.count;

        return (
        <div id="entries">
            <ul id="entries-listing" className="listing">
                {playlistEntries}
            </ul>
            <div className="info" onClick={this.handleCollapse}> 
                <div className="info-item" id="playlist-info-amount">
                    <span className="stat">{playlistSize}</span>
                    <span className="description">song{playlistSize == 1? '': 's'}<br/>in playlist</span>
                </div>
                {next}
            </div>
        </div>
        );
    }
});

var PlayerBox = React.createClass({
    getInitialState: function() {
        return {playerStatus: {}, playlistEntries: {count: 0, results: []}};
    },

    sendPlayerCommand : function(cmd) {
        $.ajax({
        url: this.props.url + "playlist/player/manage/",
        dataType: 'json',
        type: 'PUT',
        data: cmd,
        success: function(data) {
        }.bind(this),
        error: function(xhr, status, err) {
        console.error(this.props.url, status, err.toString() + xhr.responseText);
        }.bind(this)
        }); 
    },

    removeEntry : function(entryId) {
        $.ajax({
        url: this.props.url + "playlist/" + entryId + "/",
        dataType: 'json',
        type: 'DELETE',
        success: function(data) {
            this.loadStatusFromServer();
        }.bind(this),
        error: function(xhr, status, err) {
        console.error(this.props.url, status, err.toString() + xhr.responseText);
        }.bind(this)
        }); 
    },


    loadStatusFromServer: function() {
        $.ajax({
            url: this.props.url + "playlist/player/status/",
            dataType: 'json',
            cache: false,
            success: function(data) {
              this.setState({playerStatus: data});
            }.bind(this),
            error: function(xhr, status, err) {
              console.error(this.props.url, status, err.toString());
            }.bind(this)
        });
        $.ajax({
          url: this.props.url + "playlist/",
          dataType: 'json',
          cache: false,
          success: function(data) {
            this.setState({playlistEntries: data});
          }.bind(this),
          error: function(xhr, status, err) {
            console.error(this.props.url, status, err.toString());
          }.bind(this)
        });

    },

    componentDidMount: function() {
      this.loadStatusFromServer();
      setInterval(this.loadStatusFromServer, this.props.pollInterval);
    },

    render: function() {
        var playingId;
        if (this.state.playerStatus.playlist_entry){
            playingId = this.state.playerStatus.playlist_entry.id;
        }

        return (
            <div>
                <div id="playlist">
                    <Player playerStatus={this.state.playerStatus} sendPlayerCommand={this.sendPlayerCommand}/>
                    <Playlist entries={this.state.playlistEntries} playingId={playingId} removeEntry={this.removeEntry}/>
                </div>
                <div id="library">
                    <Library url={this.props.url} pollInterval={this.props.pollInterval} loadStatusFromServer={this.loadStatusFromServer}/>
                </div>
            </div>
        );
    }

}); 


ReactDOM.render(
    <PlayerBox url="/" pollInterval={1000}/>,
    document.getElementById('content')
);


