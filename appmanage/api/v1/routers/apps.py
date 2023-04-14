from typing import Optional, List

from fastapi import APIRouter, status, Depends, Query, Request
from pydantic import BaseModel, Field
from starlette.responses import JSONResponse
import os, io, sys, platform, shutil, time, subprocess, json, datetime

from api.model.app import App
from api.model.response import Response
from api.service import manage
from api.utils import shell_execute
from api.utils.common_log import myLogger
from api.exception.command_exception import CommandException

router = APIRouter()

rd1 = "code：请求操作内部响应码（0：成功 -1：失败）\n\nmessage：请求操作结果描述\n\ndata：返回请求结果内容\n\n" \
      "[\n\n" \
      "&emsp;&emsp;app_id：应用ID,\n\n" \
      "&emsp;&emsp;name：应用名,\n\n" \
      "&emsp;&emsp;customer_name：自定义应用名,\n\n" \
      "&emsp;&emsp;trade_mark：应用商标,\n\n" \
      "&emsp;&emsp;status_code：应用运行状态码,\n\n"

status = '&emsp;&emsp;status：应用运行状态,\n\n'
status_detail = "&emsp;&emsp;status：应用运行状态,（running:正常运行，stop：停止，error：错误）\n\n"
status_list = "&emsp;&emsp;status：应用运行状态,（waiting：等待安装，installing：安装中，running:正常运行，stop：停止，error：错误）\n\n"

rd2 = "&emsp;&emsp;port：应用端口,\n\n" \
      "&emsp;&emsp;volume：yml文件路径,\n\n" \
      "&emsp;&emsp;url：应用网址,\n\n" \
      "&emsp;&emsp;image_url：图片路径,\n\n" \
      "&emsp;&emsp;admin_url：管理员网址,\n\n" \
      "&emsp;&emsp;user_name：用户名,\n\n" \
      "&emsp;&emsp;password：密码,\n\n" \
      "&emsp;&emsp;official_app：是否为官方应用\n\n" \
      "]"
rd = rd1 + status + rd2
rd_detail = rd1 + status_detail + rd2
rd_list = rd1 + status_list + rd2
rd_process = "code：请求操作内部响应码（0：成功 -1：失败）\n\nmessage：请求操作结果描述\n\nstatus：应用运行状态," \
             "（pulling：拉取镜像，creating：容器启动，inting：容器初始化，running:正常运行）"
rd_two = "code：请求操作内部响应码（0：成功 -1：失败）\n\nmessage：请求操作结果描述\n\ndata：None"


@router.api_route("/AppStatus", methods=["GET", "POST"], summary="获取指定APP的信息",
                  response_description=rd_detail,
                  response_model=Response)
def app_detail(app_id: Optional[str] = Query(default=None, description="应用ID")):
    myLogger.info_logger("Receive request: /AppStatus")
    list = manage.get_app_detail(app_id)
    return JSONResponse(list)


@router.api_route("/AppList", methods=["GET", "POST"], summary="获取所有APP的信息", response_description=rd_list,
                  response_model=Response)
def list_my_apps():
    myLogger.info_logger("Receive request: /AppList")
    list = manage.get_my_app()
    return JSONResponse(content=list)


@router.api_route("/AppInstall", methods=["GET", "POST"], summary="安装APP", response_description=rd_two,
                  response_model=Response)
def AppInstall(request: Request, app_name: Optional[str] = Query(default=None, description="应用名"),
               customer_app_name: Optional[str] = Query(default=None, description="应用自定义名字"),
               app_version: Optional[str] = Query(default=None, description="应用版本")):
    
    try:
        myLogger.info_logger("Receive request: /AppInstall")
        getHeaders(request)
        ret = manage.install_app(app_name, customer_app_name, app_version)
    except CommandException as ce:
        ret = {}
        ret['ResponseData']['AppID'] = app_name + "_" + customer_app_name
        ret['Error']=manage.get_error_info("Server.Container.Error","Docker returns the original error",str(ce))
    except Exception as e:
        ret = {}
        ret['ResponseData']['AppID'] = app_name + "_" + customer_app_name
        ret['Error']=manage.get_error_info("Server.SystemError","system original error",str(ce))

    return JSONResponse(content=ret)

@router.api_route("/process", methods=["GET", "POST"], summary="获取指定APP的安装进度",
                  response_description=rd_process,
                  response_model=Response)
def install_app_process(app_id: Optional[str] = Query(default=None, description="应用ID")):
    myLogger.info_logger("Receive request: /process")
    ret = manage.install_app_process(app_id)
    return JSONResponse(content=ret)


@router.api_route("/AppStart", methods=["GET", "POST"], summary="启动APP", response_description=rd_two,
                  response_model=Response)
def start_app(app_id: Optional[str] = Query(default=None, description="应用ID")):
    myLogger.info_logger("Receive request: /AppStart")
    ret = manage.start_app(app_id)
    return JSONResponse(content=ret)


@router.api_route("/AppStop", methods=["GET", "POST"], summary="停止APP", response_description=rd_two,
                  response_model=Response)
def stop_app(app_id: Optional[str] = Query(default=None, description="应用ID")):
    myLogger.info_logger("Receive request: /AppStop")
    ret = manage.stop_app(app_id)
    return JSONResponse(content=ret)


@router.api_route("/AppRestart", methods=["GET", "POST"], summary="重启APP", response_description=rd_two,
                  response_model=Response)
def restart_app(app_id: Optional[str] = Query(default=None, description="应用ID")):
    myLogger.info_logger("Receive request: /AppRestart")
    ret = manage.restart_app(app_id)
    return JSONResponse(content=ret)


@router.api_route("/AppUninstall", methods=["GET", "POST"], summary="卸载APP", response_description=rd_two,
                  response_model=Response)
def uninstall_app(request: Request, app_id: Optional[str] = Query(default=None, description="应用ID"),
                 delete_image: bool = Query(default=False, description="是否删除镜像"),
                 delete_data: bool = Query(default=True, description='是否删除所有数据')):
    myLogger.info_logger("Receive request: /AppUninstall")
    getHeaders(request)
    ret = manage.uninstall_app(app_id, delete_image, delete_data)
    return JSONResponse(content=ret)


def getHeaders(request):
    headers = request.headers
    try:
        version = headers.get('Version')
        language = headers.get('Language')
        myLogger.info_logger("Version: " + version + ", Language: " + language)
    except:
        pass
