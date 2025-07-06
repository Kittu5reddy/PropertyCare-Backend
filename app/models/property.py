from sqlalchemy import Column, Integer, String, Enum, Text, ForeignKey, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum
from models import Base


def generate_plot_id(plot_id):
    return f""



# Enum for plot types
class PlotTypeEnum(enum.Enum):
    open_plot = "open-plot"
    commercial = "commercial"
    farm_land = "farm-land"
    hmda = "HMDA"
    dtcp = "DTCP"
    gp = "GP"
    others = "others"

class Plot(Base):
    __tablename__ = 'plots'
    id = Column(Integer, primary_key=True, index=True)
    property_id=Column(Integer, primary_key=True, index=True)
    project_name = Column(String, nullable=False)
    survey_number = Column(String, nullable=True)
    plot_number = Column(String, nullable=True)
    village/city=Column(String, nullable=False)
    mandal=Column(String, nullable=False)
    distict=Column(String, nullable=False)
    state=Column(String, nullable=False)
    extent = Column(String, nullable=False)  # e.g., "200 Sq.Yards"
    facing = Column(String, nullable=False)  # East/West/North/South
    owner_name = Column(String, nullable=False)
    owner_contact = Column(String, nullable=False)
    landmark = Column(String, nullable=True)
    plot_type = Column(Enum(PlotTypeEnum), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

class Document(Base):
    __tablename__ = 'documents'
    id = Column(Integer, primary_key=True, index=True)
    plot_id = Column(Integer, ForeignKey('plots.property_id'), nullable=False)
    doc_type = Column(String, nullable=False)  # e.g., sale_deed, ec, patta, etc.
    file_url = Column(String, nullable=False)  # File path or cloud URL
    uploaded_by = Column(String, nullable=True)  # optional user/email
    is_mandatory = Column(Boolean, default=False)
    uploaded_at = Column(DateTime(timezone=True), server_default=func.now())
