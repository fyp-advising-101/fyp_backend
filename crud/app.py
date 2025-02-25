from flask import Flask, json, request, jsonify
from flask_cors import CORS
import sys, os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from shared.models.base import Base
from shared.models.job import Job
from shared.models.scrape_target import ScrapeTarget
from shared.models.media_gen_options import MediaGenOptions
from shared.models.media_category_options import MediaCategoryOptions
from shared.database import engine, SessionLocal
import datetime

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})
# Create tables if not created
Base.metadata.create_all(bind=engine)

@app.route('/jobs', methods=['POST'])
def add_job():
    """Add a new job to the scheduler"""
    data = request.json
    db_session = SessionLocal()
    
    try:
        new_job = Job(
            task_name=data['task_name'],
            task_id = data['task_id'],
            scheduled_date=datetime.datetime.strptime(data['scheduled_date'], "%Y-%m-%d %H:%M:%S"),
            status=0,
            error_message=data.get('error_message', None),
            created_at=datetime.datetime.now(),
            updated_at=datetime.datetime.now()
        )
        db_session.add(new_job)
        db_session.commit()
        return jsonify({"message": "Job added successfully", "job_id": new_job.id}), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/jobs/<int:job_id>', methods=['PUT'])
def edit_job(job_id):
    """Edit an existing job"""
    data = request.json
    db_session = SessionLocal()
    job = db_session.query(Job).filter_by(id=job_id).first()
    if not job:
        return jsonify({"error": "Job not found"}), 404

    try:
        job.task_name = data.get('task_name', job.task_name)
        job.task_id = data.get('task_id', job.task_id)
        job.scheduled_date = datetime.datetime.strptime(data['scheduled_date'], "%Y-%m-%d %H:%M:%S") if 'scheduled_date' in data else job.scheduled_date
        job.status = data.get('status', job.status)
        job.error_message = data.get('error_message', job.error_message)
        job.updated_at = datetime.datetime.now()

        db_session.commit()
        return jsonify({"message": "Job updated successfully"})
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/jobs/<int:job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Delete a job from the scheduler"""
    db_session = SessionLocal()
    job = db_session.query(Job).filter_by(id=job_id).first()
    if not job:
        return jsonify({"error": "Job not found"}), 404

    try:
        db_session.delete(job)
        db_session.commit()
        return jsonify({"message": "Job deleted successfully"})
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/jobs/<int:job_id>', methods=['GET'])
def get_job(job_id):
    """Get a single job by ID"""
    db_session = SessionLocal()
    job = db_session.query(Job).filter_by(id=job_id).first()
    if not job:
        return jsonify({"error": "Job not found"}), 404

    return jsonify({
        "id": job.id,
        "task_name": job.task_name,
        "task_id": job.task_id,
        "scheduled_date": job.scheduled_date.strftime("%Y-%m-%d %H:%M:%S"),
        "status": job.status,
        "error_message": job.error_message,
        "created_at": job.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        "updated_at": job.updated_at.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/jobs', methods=['GET'])
def get_all_jobs():
    """Get all jobs from the scheduler"""
    db_session = SessionLocal()
    jobs = db_session.query(Job).all()
    return jsonify([
        {
            "id": job.id,
            "task_name": job.task_name,
            "task_id": job.task_id,
            "scheduled_date": job.scheduled_date.strftime("%Y-%m-%d %H:%M:%S"),
            "status": job.status,
            "error_message": job.error_message,
            "created_at": job.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            "updated_at": job.updated_at.strftime("%Y-%m-%d %H:%M:%S")
        } for job in jobs
    ])

@app.route('/scrape-targets', methods=['POST'])
def add_scrape_target():
    """Add a new scrape target"""
    db_session = SessionLocal()
    data = request.json
    try:
        new_target = ScrapeTarget(
            name=data['name'],
            url=data['url'],
            type=data['type'],
            frequency=data['frequency'],
            created_at=datetime.datetime.now()
        )
        db_session.add(new_target)
        db_session.commit()
        return jsonify({"message": "Scrape target added successfully", "target_id": new_target.id}), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/scrape-targets/<int:target_id>', methods=['PUT'])
def edit_scrape_target(target_id):
    """Edit an existing scrape target"""
    data = request.json
    db_session = SessionLocal()
    target = db_session.query(ScrapeTarget).filter_by(id=target_id).first()
    if not target:
        return jsonify({"error": "Scrape target not found"}), 404

    try:
        target.name = data.get('name', target.name)
        target.url = data.get('url', target.url)
        target.type = data.get('type', target.type)
        target.frequency = data.get('frequency', target.type)

        db_session.commit()
        return jsonify({"message": "Scrape target updated successfully"})
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/scrape-targets/<int:target_id>', methods=['DELETE'])
def delete_scrape_target(target_id):
    """Delete a scrape target"""
    db_session = SessionLocal()
    target = db_session.query(ScrapeTarget).filter_by(id=target_id).first()
    if not target:
        return jsonify({"error": "Scrape target not found"}), 404

    try:
        db_session.delete(target)
        db_session.commit()
        return jsonify({"message": "Scrape target deleted successfully"})
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/scrape-targets/<int:target_id>', methods=['GET'])
def get_scrape_target(target_id):
    """Get a single scrape target by ID"""
    db_session = SessionLocal()
    target = db_session.query(ScrapeTarget).filter_by(id=target_id).first()
    if not target:
        return jsonify({"error": "Scrape target not found"}), 404

    return jsonify({
        "id": target.id,
        "name": target.name,
        "url": target.url,
        "type": target.type,
        "frequency" : target.frequency,
        "created_at": target.created_at.strftime("%Y-%m-%d %H:%M:%S")
    })

@app.route('/scrape-targets', methods=['GET'])
def get_all_scrape_targets():
    """Get all scrape targets"""
    db_session = SessionLocal()
    targets = db_session.query(ScrapeTarget).all()
    return jsonify([
        {
            "id": target.id,
            "name": target.name,
            "url": target.url,
            "type": target.type,
            "frequency" : target.frequency,
            "created_at": target.created_at.strftime("%Y-%m-%d %H:%M:%S")
        } for target in targets
    ])

@app.route('/media-gen-options', methods=['POST'])
def add_media_gen_option():
    """Add a new media generation option"""
    data = request.json
    db_session = SessionLocal()
    try:
        new_option = MediaGenOptions(
            category=data['category'],
            description=data.get('description', None),
            media_type=data.get('media_type', None),
        )
        db_session.add(new_option)
        db_session.commit()
        return jsonify({"message": "Media generation option added successfully", "option_id": new_option.id}), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/media-gen-options/<int:option_id>', methods=['GET'])
def get_media_gen_option(option_id):
    """Get a single media generation option by ID"""
    db_session = SessionLocal()
    option = db_session.query(MediaGenOptions).filter_by(id=option_id).first()
    if not option:
        return jsonify({"error": "Media generation option not found"}), 404

    return jsonify({
        "id": option.id,
        "category": option.category,
        "description": option.description,
        "media_type": option.media_type,
    })

@app.route('/media-gen-options', methods=['GET'])
def get_all_media_gen_options():
    """Get all media generation options"""
    db_session = SessionLocal()
    options = db_session.query(MediaGenOptions).all()
    return jsonify([
        {
            "id": option.id,
            "category": option.category,
            "description": option.description,
            "media_type": option.media_type,
        } for option in options
    ])

@app.route('/media-gen-options/<int:option_id>', methods=['PUT'])
def edit_media_gen_option(option_id):
    """Edit an existing media generation option"""
    data = request.json
    db_session = SessionLocal()
    option = db_session.query(MediaGenOptions).filter_by(id=option_id).first()
    if not option:
        return jsonify({"error": "Media generation option not found"}), 404

    try:
        option.category = data.get('category', option.category)
        option.description = data.get('description', option.description)
        option.media_type = data.get('media_type', option.media_type)

        db_session.commit()
        return jsonify({"message": "Media generation option updated successfully"})
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/media-gen-options/<int:option_id>', methods=['DELETE'])
def delete_media_gen_option(option_id):
    """Delete a media generation option"""
    db_session = SessionLocal()
    option = db_session.query(MediaGenOptions).filter_by(id=option_id).first()
    if not option:
        return jsonify({"error": "Media generation option not found"}), 404

    try:
        db_session.delete(option)
        db_session.commit()
        return jsonify({"message": "Media generation option deleted successfully"})
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 400
    
@app.route('/media-gen-options/<int:option_id>/category-options', methods=['GET'])
def get_category_options_from_media_gen_option(option_id):
    """Get all media category options for a specific media generation option"""
    db_session = SessionLocal()
    
    # Optionally, first check if the media generation option exists
    media_gen_option = db_session.query(MediaGenOptions).filter_by(id=option_id).first()
    if not media_gen_option:
        return jsonify({"error": "Media generation option not found"}), 404

    # Retrieve all category options associated with the given media generation option
    category_options = db_session.query(MediaCategoryOptions).filter_by(option_id=option_id).all()

    result = [{
        "id": option.id,
        "title": option.title,
        "prompt_text": option.prompt_text,
        "option_id": option.option_id
    } for option in category_options]

    return jsonify(result)


@app.route('/media-category-options', methods=['POST'])
def add_media_category_option():
    """Add a new media category option"""
    data = request.json
    db_session = SessionLocal()
    try:
        new_option = MediaCategoryOptions(
            title=data['title'],
            prompt_text=data['prompt_text'],
            option_id=data['option_id']  # This links to the parent media gen option
        )
        db_session.add(new_option)
        db_session.commit()
        return jsonify({
            "message": "Media category option added successfully",
            "option_id": new_option.id
        }), 201
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/media-category-options/<int:option_id>', methods=['GET'])
def get_media_category_option(option_id):
    """Get a single media category option by ID"""
    db_session = SessionLocal()
    option = db_session.query(MediaCategoryOptions).filter_by(id=option_id).first()
    if not option:
        return jsonify({"error": "Media category option not found"}), 404

    return jsonify({
        "id": option.id,
        "title": option.title,
        "prompt_text": option.prompt_text,
        "option_id": option.option_id
    })

@app.route('/media-category-options', methods=['GET'])
def get_all_media_category_options():
    """Get all media category options"""
    db_session = SessionLocal()
    options = db_session.query(MediaCategoryOptions).all()
    return jsonify([
        {
            "id": option.id,
            "title": option.title,
            "prompt_text": option.prompt_text,
            "option_id": option.option_id
        } for option in options
    ])

@app.route('/media-category-options/<int:option_id>', methods=['PUT'])
def edit_media_category_option(option_id):
    """Edit an existing media category option"""
    data = request.json
    db_session = SessionLocal()
    option = db_session.query(MediaCategoryOptions).filter_by(id=option_id).first()
    if not option:
        return jsonify({"error": "Media category option not found"}), 404

    try:
        option.title = data.get('title', option.title)
        option.prompt_text = data.get('prompt_text', option.prompt_text)
        option.option_id = data.get('option_id', option.option_id)
        db_session.commit()
        return jsonify({"message": "Media category option updated successfully"})
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 400

@app.route('/media-category-options/<int:option_id>', methods=['DELETE'])
def delete_media_category_option(option_id):
    """Delete a media category option"""
    db_session = SessionLocal()
    option = db_session.query(MediaCategoryOptions).filter_by(id=option_id).first()
    if not option:
        return jsonify({"error": "Media category option not found"}), 404

    try:
        db_session.delete(option)
        db_session.commit()
        return jsonify({"message": "Media category option deleted successfully"})
    except Exception as e:
        db_session.rollback()
        return jsonify({"error": str(e)}), 400


if __name__ == '__main__':
    app.run(host="0.0.0.0", port=3001)