new Vue({
    el:'#app',
    delimiters: ['[[', ']]'],
    template:`
        <!--Application-->
        <center>
        <div class="card bg-light" style='max-width:540px;'>
            <div class="row g-0">
                <div class="col-md-4">
                    <div>
                        <img src="../static/pic.jpg" width='50%'  alt="Marcus-Aurelius">
                        <p class="text-muted" style='font-size:12px;'> Image by Eric Gaba, licensed under <a href="https://creativecommons.org/licenses/by-sa/3.0/" target='_blank'>CC-By-SA 3.0</a></p>
                    </div>
                </div>
                <div class="col-md-8">
            <div class="card-body ">
        <div class="card-text" v-model='answer'>[[ answer ]]</div>
                    </div>
                </div>
            </div>
        <br>
    <input class="form-control" v-model='question'  placeholder="Type here"></input><button v-on:click='getAnswer' class="mt-2 btn btn-danger">Say it!</button>
        </div>
        </center>
    `,

    data: {answer: '' , question: ''} ,

    methods: {
        getAnswer(){
            const req = new XMLHttpRequest();
            const url = window.location 
            const question = this.question

            req.open('POST', url, false)
            req.send(question)

            this.answer = req.responseText
        }

    }

})
