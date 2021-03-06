import os
from flask import Flask, request, abort, jsonify, app
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
import random

from trivia_api.starter.backend.models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10


def paginate_questions(request, selection):
    page = request.args.get('page', 1, type=int)
    start = (page - 1) * QUESTIONS_PER_PAGE
    end = start + QUESTIONS_PER_PAGE

    questions = [question.format() for question in selection]
    current_questions = questions[start:end]

    return current_questions


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    setup_db(app)
    CORS(app)

    CORS(app, resources={'/': {'origins': '*'}})


    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        response.headers.add('Access-Control-Allow-Headers', 'GET, POST, PATCH, DELETE, OPTION')
        return response


    @app.route('/categories')
    def get_categories():
        categories = Category.query.all()
        result = {}
        for i in categories:
            result[i.id] = i.type
        if len(result == 0):
            abort(404)
        return jsonify({
            'success': True,
            'categories': result
        })


    @app.route('/questions')
    def get_questions():
        questions = Question.query.all()
        num_of_question = len(questions)
        paginated_questions = paginate_questions(request, questions)

        categories = Category.query.all()
        dict_categories = {}
        for i in categories:
            dict_categories[i.id] = i.type

        if num_of_question == 0:
            abort(404)

        return jsonify({
            'success': True,
            'questions': paginated_questions,
            'total_questions': num_of_question,
            'categories': dict_categories
        })


    @app.route('/questions/<int:qid>', methods=['DELETE'])
    def delete_question(qid):
        try:
            question = Question.query.filter_by(id=qid).one_or_none()

            if question is None:
                abort(404)

            question.delete()

            return jsonify({
                'success': True,
                'deleted': id
            })
        except:
            abort(422)

    @app.route('/questions', methods=['POST'])
    def post_or_search_question():
        req = request.get_json()
        if req.get('searchTerm'):
            search_term = req.get('searchTerm')

            questions = Question.query.filter(
                Question.question.ilike(f'%{search_term}%')).all()
            if len(questions) == 0:
                abort(404)

            paginated = paginate_questions(request, questions)

            return jsonify({
                'success': True,
                'questions': paginated,
                'total_questions': len(Question.query.all())
            })
        else:
            new_question = req.get('question')
            new_answer = req.get('answer')
            new_difficulty = req.get('difficulty')
            new_category = req.get('category')

            if ((new_question is None) or (new_answer is None)
                    or (new_difficulty is None) or (new_category is None)):
                abort(422)

            try:
                question = Question(question=new_question, answer=new_answer,
                                    difficulty=new_difficulty, category=new_category)
                question.insert()
                questions = Question.query.order_by(Question.id).all()
                paginated_questions = paginate_questions(request, questions)

                # return data to view
                return jsonify({
                    'success': True,
                    'created': question.id,
                    'question_created': question.question,
                    'questions': paginated_questions,
                    'total_questions': len(Question.query.all())
                })
            except:
                abort(422)

    @app.route('/categories/<int:cid>/questions', methods=['GET'])
    def get_questions_by_category(cid):
        try:
            category = Category.query.filter_by(id=cid).one_or_none()

            if category is None:
                abort(400)

            questions = Question.query.filter_by(category=category.id).all()

            paginated_questions = paginate_questions(request, questions)

            return jsonify({
                'success': True,
                'questions': paginated_questions,
                'total_questions': len(Question.query.all()),
                'current_category': category.type
            })
        except:
            abort(422)

    @app.route('/quizzes', methods=['POST'])
    def get_quiz_question():

        req = request.get_json()

        previous = req.get('previous_questions')

        category = req.get('quiz_category')

        if (category is None) or (previous is None):
            abort(400)

        if category['id'] == 0:
            questions = Question.query.all()
        else:
            questions = Question.query.filter_by(category=category['id']).all()

        total = len(questions)

        def get_random_question():
            return questions[random.randrange(0, len(questions), 1)]

        def check_if_used(question):
            used = False
            for q in previous:
                if q == question.id:
                    used = True

            return used

        question = get_random_question()

        while check_if_used(question):
            question = get_random_question()

            if len(previous) == total:
                return jsonify({
                    'success': True
                })

        return jsonify({
            'success': True,
            'question': question.format()
        })

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": "bad request"
        }), 400

    return app

