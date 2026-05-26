var VoiceManager = (function() {
    var voiceEnabled = true;
    var synth = window.speechSynthesis;
    var voices = [];
    
    function loadVoices() {
        voices = synth.getVoices();
    }
    
    if (synth) {
        loadVoices();
        if (synth.onvoiceschanged !== undefined) {
            synth.onvoiceschanged = loadVoices;
        }
    }
    
    function getChineseVoice() {
        for (var i = 0; i < voices.length; i++) {
            if (voices[i].lang === 'zh-CN' || voices[i].lang === 'zh') {
                return voices[i];
            }
        }
        for (var i = 0; i < voices.length; i++) {
            if (voices[i].name.includes('Chinese') || voices[i].name.includes('中文')) {
                return voices[i];
            }
        }
        return null;
    }
    
    return {
        voiceEnabled: voiceEnabled,
        
        speak: function(text) {
            if (!voiceEnabled || !synth) {
                return;
            }
            
            this.stop();
            
            var utterance = new SpeechSynthesisUtterance(text);
            utterance.lang = 'zh-CN';
            utterance.rate = 0.9;
            utterance.pitch = 1;
            utterance.volume = 0.8;
            
            var voice = getChineseVoice();
            if (voice) {
                utterance.voice = voice;
            }
            
            synth.speak(utterance);
        },
        
        stop: function() {
            if (synth) {
                synth.cancel();
            }
        },
        
        voiceOn: function() {
            voiceEnabled = true;
            this.voiceEnabled = true;
        },
        
        voiceOff: function() {
            this.stop();
            voiceEnabled = false;
            this.voiceEnabled = false;
        },
        
        voiceToggle: function() {
            if (voiceEnabled) {
                this.voiceOff();
                return false;
            } else {
                this.voiceOn();
                return true;
            }
        },
        
        isEnabled: function() {
            return voiceEnabled;
        }
    };
})();

var VoiceHelper = {
    sayWelcome: function(username) {
        VoiceManager.speak('欢迎回来，' + username + '，今天也要加油哦！');
    },
    
    sayLoginSuccess: function() {
        VoiceManager.speak('登录成功，欢迎使用系统');
    },
    
    sayLogout: function() {
        VoiceManager.speak('已安全退出，下次再见');
    },
    
    saySaveSuccess: function() {
        VoiceManager.speak('保存成功');
    },
    
    sayDeleteSuccess: function() {
        VoiceManager.speak('删除成功');
    },
    
    sayOperationSuccess: function() {
        VoiceManager.speak('操作成功');
    },
    
    sayWarning: function(msg) {
        VoiceManager.speak('注意：' + msg);
    },
    
    sayError: function(msg) {
        VoiceManager.speak('错误：' + msg);
    },
    
    sayInfo: function(msg) {
        VoiceManager.speak(msg);
    }
};
