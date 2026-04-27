# -*- coding: utf-8 -*-
import threading
import time

from dxGame.dx_core import *
from dxGame import dxpyd, Window, MiniOpenCV
import comtypes

def get_scale_factor_for_monitor(hmonitor):
    scale_factor = wintypes.UINT()
    ctypes.windll.shcore.GetScaleFactorForMonitor(hmonitor, ctypes.byref(scale_factor))

    return scale_factor.value / 100.0


class DISPLAY_DEVICE(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("DeviceName", wintypes.WCHAR * 32),
        ("DeviceString", wintypes.WCHAR * 128),
        ("StateFlags", wintypes.DWORD),
        ("DeviceID", wintypes.WCHAR * 128),
        ("DeviceKey", wintypes.WCHAR * 128),
    ]


def get_display_device_name_mapping():
    display_names = list()

    i = 0
    while True:
        display_device = DISPLAY_DEVICE()
        display_device.cb = ctypes.sizeof(display_device)

        if not ctypes.windll.user32.EnumDisplayDevicesW(None, i, ctypes.byref(display_device), 0):
            break

        if display_device.StateFlags > 0:
            is_primary_display_device = bool(display_device.StateFlags & 4)
            display_names.append((display_device.DeviceName, is_primary_display_device))

        i += 1

    display_device_name_mapping = dict()

    for display_name, is_primary in display_names:
        display_device = DISPLAY_DEVICE()
        display_device.cb = ctypes.sizeof(display_device)

        if ctypes.windll.user32.EnumDisplayDevicesW(
                display_name, 0, ctypes.byref(display_device), 0
        ):
            display_device_name_mapping[display_name.split("\\")[-1]] = (
                display_device.DeviceString,
                is_primary,
            )

    return display_device_name_mapping


def get_hmonitor_by_point(x, y):
    point = wintypes.POINT()

    point.x = x
    point.y = y

    return ctypes.windll.user32.MonitorFromPoint(point, 0)


class DXGI_SAMPLE_DESC(ctypes.Structure):
    _fields_ = [
        ("Count", wintypes.UINT),
        ("Quality", wintypes.UINT),
    ]


class D3D11_BOX(ctypes.Structure):
    _fields_ = [
        ("left", wintypes.UINT),
        ("top", wintypes.UINT),
        ("front", wintypes.UINT),
        ("right", wintypes.UINT),
        ("bottom", wintypes.UINT),
        ("back", wintypes.UINT),
    ]


class D3D11_TEXTURE2D_DESC(ctypes.Structure):
    _fields_ = [
        ("Width", wintypes.UINT),
        ("Height", wintypes.UINT),
        ("MipLevels", wintypes.UINT),
        ("ArraySize", wintypes.UINT),
        ("Format", wintypes.UINT),
        ("SampleDesc", DXGI_SAMPLE_DESC),
        ("Usage", wintypes.UINT),
        ("BindFlags", wintypes.UINT),
        ("CPUAccessFlags", wintypes.UINT),
        ("MiscFlags", wintypes.UINT),
    ]


class ID3D11DeviceChild(comtypes.IUnknown):
    _iid_ = comtypes.GUID("{1841e5c8-16b0-489b-bcc8-44cfb0d5deae}")
    _methods_ = [
        comtypes.STDMETHOD(None, "GetDevice"),
        comtypes.STDMETHOD(comtypes.HRESULT, "GetPrivateData"),
        comtypes.STDMETHOD(comtypes.HRESULT, "SetPrivateData"),
        comtypes.STDMETHOD(comtypes.HRESULT, "SetPrivateDataInterface"),
    ]


class ID3D11Resource(ID3D11DeviceChild):
    _iid_ = comtypes.GUID("{dc8e63f3-d12b-4952-b47b-5e45026a862d}")
    _methods_ = [
        comtypes.STDMETHOD(None, "GetType"),
        comtypes.STDMETHOD(None, "SetEvictionPriority"),
        comtypes.STDMETHOD(wintypes.UINT, "GetEvictionPriority"),
    ]


class ID3D11Texture2D(ID3D11Resource):
    _iid_ = comtypes.GUID("{6f15aaf2-d208-4e89-9ab4-489535d34f9c}")
    _methods_ = [
        comtypes.STDMETHOD(None, "GetDesc", [ctypes.POINTER(D3D11_TEXTURE2D_DESC)]),
    ]


class ID3D11DeviceContext(ID3D11DeviceChild):
    _iid_ = comtypes.GUID("{c0bfa96c-e089-44fb-8eaf-26f8796190da}")
    _methods_ = [
        comtypes.STDMETHOD(None, "VSSetConstantBuffers"),
        comtypes.STDMETHOD(None, "PSSetShaderResources"),
        comtypes.STDMETHOD(None, "PSSetShader"),
        comtypes.STDMETHOD(None, "PSSetSamplers"),
        comtypes.STDMETHOD(None, "VSSetShader"),
        comtypes.STDMETHOD(None, "DrawIndexed"),
        comtypes.STDMETHOD(None, "Draw"),
        comtypes.STDMETHOD(comtypes.HRESULT, "Map"),
        comtypes.STDMETHOD(None, "Unmap"),
        comtypes.STDMETHOD(None, "PSSetConstantBuffers"),
        comtypes.STDMETHOD(None, "IASetInputLayout"),
        comtypes.STDMETHOD(None, "IASetVertexBuffers"),
        comtypes.STDMETHOD(None, "IASetIndexBuffer"),
        comtypes.STDMETHOD(None, "DrawIndexedInstanced"),
        comtypes.STDMETHOD(None, "DrawInstanced"),
        comtypes.STDMETHOD(None, "GSSetConstantBuffers"),
        comtypes.STDMETHOD(None, "GSSetShader"),
        comtypes.STDMETHOD(None, "IASetPrimitiveTopology"),
        comtypes.STDMETHOD(None, "VSSetShaderResources"),
        comtypes.STDMETHOD(None, "VSSetSamplers"),
        comtypes.STDMETHOD(None, "Begin"),
        comtypes.STDMETHOD(None, "End"),
        comtypes.STDMETHOD(comtypes.HRESULT, "GetData"),
        comtypes.STDMETHOD(None, "SetPredication"),
        comtypes.STDMETHOD(None, "GSSetShaderResources"),
        comtypes.STDMETHOD(None, "GSSetSamplers"),
        comtypes.STDMETHOD(None, "OMSetRenderTargets"),
        comtypes.STDMETHOD(None, "OMSetRenderTargetsAndUnorderedAccessViews"),
        comtypes.STDMETHOD(None, "OMSetBlendState"),
        comtypes.STDMETHOD(None, "OMSetDepthStencilState"),
        comtypes.STDMETHOD(None, "SOSetTargets"),
        comtypes.STDMETHOD(None, "DrawAuto"),
        comtypes.STDMETHOD(None, "DrawIndexedInstancedIndirect"),
        comtypes.STDMETHOD(None, "DrawInstancedIndirect"),
        comtypes.STDMETHOD(None, "Dispatch"),
        comtypes.STDMETHOD(None, "DispatchIndirect"),
        comtypes.STDMETHOD(None, "RSSetState"),
        comtypes.STDMETHOD(None, "RSSetViewports"),
        comtypes.STDMETHOD(None, "RSSetScissorRects"),
        comtypes.STDMETHOD(
            None,
            "CopySubresourceRegion",
            [
                ctypes.POINTER(ID3D11Resource),
                wintypes.UINT,
                wintypes.UINT,
                wintypes.UINT,
                wintypes.UINT,
                ctypes.POINTER(ID3D11Resource),
                wintypes.UINT,
                ctypes.POINTER(D3D11_BOX),
            ],
        ),
        comtypes.STDMETHOD(
            None, "CopyResource", [ctypes.POINTER(ID3D11Resource), ctypes.POINTER(ID3D11Resource)],
        ),
        comtypes.STDMETHOD(None, "UpdateSubresource"),
        comtypes.STDMETHOD(None, "CopyStructureCount"),
        comtypes.STDMETHOD(None, "ClearRenderTargetView"),
        comtypes.STDMETHOD(None, "ClearUnorderedAccessViewUint"),
        comtypes.STDMETHOD(None, "ClearUnorderedAccessViewFloat"),
        comtypes.STDMETHOD(None, "ClearDepthStencilView"),
        comtypes.STDMETHOD(None, "GenerateMips"),
        comtypes.STDMETHOD(None, "SetResourceMinLOD"),
        comtypes.STDMETHOD(wintypes.FLOAT, "GetResourceMinLOD"),
        comtypes.STDMETHOD(None, "ResolveSubresource"),
        comtypes.STDMETHOD(None, "ExecuteCommandList"),
        comtypes.STDMETHOD(None, "HSSetShaderResources"),
        comtypes.STDMETHOD(None, "HSSetShader"),
        comtypes.STDMETHOD(None, "HSSetSamplers"),
        comtypes.STDMETHOD(None, "HSSetConstantBuffers"),
        comtypes.STDMETHOD(None, "DSSetShaderResources"),
        comtypes.STDMETHOD(None, "DSSetShader"),
        comtypes.STDMETHOD(None, "DSSetSamplers"),
        comtypes.STDMETHOD(None, "DSSetConstantBuffers"),
        comtypes.STDMETHOD(None, "CSSetShaderResources"),
        comtypes.STDMETHOD(None, "CSSetUnorderedAccessViews"),
        comtypes.STDMETHOD(None, "CSSetShader"),
        comtypes.STDMETHOD(None, "CSSetSamplers"),
        comtypes.STDMETHOD(None, "CSSetConstantBuffers"),
        comtypes.STDMETHOD(None, "VSGetConstantBuffers"),
        comtypes.STDMETHOD(None, "PSGetShaderResources"),
        comtypes.STDMETHOD(None, "PSGetShader"),
        comtypes.STDMETHOD(None, "PSGetSamplers"),
        comtypes.STDMETHOD(None, "VSGetShader"),
        comtypes.STDMETHOD(None, "PSGetConstantBuffers"),
        comtypes.STDMETHOD(None, "IAGetInputLayout"),
        comtypes.STDMETHOD(None, "IAGetVertexBuffers"),
        comtypes.STDMETHOD(None, "IAGetIndexBuffer"),
        comtypes.STDMETHOD(None, "GSGetConstantBuffers"),
        comtypes.STDMETHOD(None, "GSGetShader"),
        comtypes.STDMETHOD(None, "IAGetPrimitiveTopology"),
        comtypes.STDMETHOD(None, "VSGetShaderResources"),
        comtypes.STDMETHOD(None, "VSGetSamplers"),
        comtypes.STDMETHOD(None, "GetPredication"),
        comtypes.STDMETHOD(None, "GSGetShaderResources"),
        comtypes.STDMETHOD(None, "GSGetSamplers"),
        comtypes.STDMETHOD(None, "OMGetRenderTargets"),
        comtypes.STDMETHOD(None, "OMGetRenderTargetsAndUnorderedAccessViews"),
        comtypes.STDMETHOD(None, "OMGetBlendState"),
        comtypes.STDMETHOD(None, "OMGetDepthStencilState"),
        comtypes.STDMETHOD(None, "SOGetTargets"),
        comtypes.STDMETHOD(None, "RSGetState"),
        comtypes.STDMETHOD(None, "RSGetViewports"),
        comtypes.STDMETHOD(None, "RSGetScissorRects"),
        comtypes.STDMETHOD(None, "HSGetShaderResources"),
        comtypes.STDMETHOD(None, "HSGetShader"),
        comtypes.STDMETHOD(None, "HSGetSamplers"),
        comtypes.STDMETHOD(None, "HSGetConstantBuffers"),
        comtypes.STDMETHOD(None, "DSGetShaderResources"),
        comtypes.STDMETHOD(None, "DSGetShader"),
        comtypes.STDMETHOD(None, "DSGetSamplers"),
        comtypes.STDMETHOD(None, "DSGetConstantBuffers"),
        comtypes.STDMETHOD(None, "CSGetShaderResources"),
        comtypes.STDMETHOD(None, "CSGetUnorderedAccessViews"),
        comtypes.STDMETHOD(None, "CSGetShader"),
        comtypes.STDMETHOD(None, "CSGetSamplers"),
        comtypes.STDMETHOD(None, "CSGetConstantBuffers"),
        comtypes.STDMETHOD(None, "ClearState"),
        comtypes.STDMETHOD(None, "Flush"),
        comtypes.STDMETHOD(None, "GetType"),
        comtypes.STDMETHOD(wintypes.UINT, "GetContextFlags"),
        comtypes.STDMETHOD(comtypes.HRESULT, "FinishCommandList"),
    ]


class ID3D11Device(comtypes.IUnknown):
    _iid_ = comtypes.GUID("{db6f6ddb-ac77-4e88-8253-819df9bbf140}")
    _methods_ = [
        comtypes.STDMETHOD(comtypes.HRESULT, "CreateBuffer"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CreateTexture1D"),
        comtypes.STDMETHOD(
            comtypes.HRESULT,
            "CreateTexture2D",
            [
                ctypes.POINTER(D3D11_TEXTURE2D_DESC),
                ctypes.POINTER(None),
                ctypes.POINTER(ctypes.POINTER(ID3D11Texture2D)),
            ],
        ),
        comtypes.STDMETHOD(comtypes.HRESULT, "CreateTexture3D"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CreateShaderResourceView"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CreateUnorderedAccessView"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CreateRenderTargetView"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CreateDepthStencilView"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CreateInputLayout"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CreateVertexShader"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CreateGeometryShader"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CreateGeometryShaderWithStreamOutput"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CreatePixelShader"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CreateHullShader"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CreateDomainShader"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CreateComputeShader"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CreateClassLinkage"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CreateBlendState"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CreateDepthStencilState"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CreateRasterizerState"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CreateSamplerState"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CreateQuery"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CreatePredicate"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CreateCounter"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CreateDeferredContext"),
        comtypes.STDMETHOD(comtypes.HRESULT, "OpenSharedResource"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CheckFormatSupport"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CheckMultisampleQualityLevels"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CheckCounterInfo"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CheckCounter"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CheckFeatureSupport"),
        comtypes.STDMETHOD(comtypes.HRESULT, "GetPrivateData"),
        comtypes.STDMETHOD(comtypes.HRESULT, "SetPrivateData"),
        comtypes.STDMETHOD(comtypes.HRESULT, "SetPrivateDataInterface"),
        comtypes.STDMETHOD(ctypes.c_int32, "GetFeatureLevel"),
        comtypes.STDMETHOD(ctypes.c_uint, "GetCreationFlags"),
        comtypes.STDMETHOD(comtypes.HRESULT, "GetDeviceRemovedReason"),
        comtypes.STDMETHOD(
            None, "GetImmediateContext", [ctypes.POINTER(ctypes.POINTER(ID3D11DeviceContext))],
        ),
        comtypes.STDMETHOD(comtypes.HRESULT, "SetExceptionMode"),
        comtypes.STDMETHOD(ctypes.c_uint, "GetExceptionMode"),
    ]


def initialize_d3d_device(dxgi_adapter):
    initialize_func = ctypes.windll.d3d11.D3D11CreateDevice

    feature_levels = [45312, 45056, 41216, 40960, 37632, 37376, 37120]

    d3d_device = ctypes.POINTER(ID3D11Device)()
    d3d_device_context = ctypes.POINTER(ID3D11DeviceContext)()

    initialize_func(
        dxgi_adapter,
        0,
        None,
        0,
        ctypes.byref((ctypes.c_uint * 7)(*feature_levels)),
        len(feature_levels),
        7,
        ctypes.byref(d3d_device),
        None,
        ctypes.byref(d3d_device_context),
    )

    return d3d_device, d3d_device_context


def describe_d3d11_texture_2d(d3d11_texture_2d):
    d3d11_texture_2d_description = D3D11_TEXTURE2D_DESC()
    d3d11_texture_2d.GetDesc(ctypes.byref(d3d11_texture_2d_description))

    return d3d11_texture_2d_description


def prepare_d3d11_texture_2d_for_cpu(d3d11_texture_2d, d3d_device):
    d3d11_texture_2d_description = describe_d3d11_texture_2d(d3d11_texture_2d)

    d3d11_texture_2d_description_cpu = D3D11_TEXTURE2D_DESC()

    d3d11_texture_2d_description_cpu.Width = d3d11_texture_2d_description.Width
    d3d11_texture_2d_description_cpu.Height = d3d11_texture_2d_description.Height
    d3d11_texture_2d_description_cpu.MipLevels = 1
    d3d11_texture_2d_description_cpu.ArraySize = 1
    d3d11_texture_2d_description_cpu.SampleDesc.Count = 1
    d3d11_texture_2d_description_cpu.SampleDesc.Quality = 0
    d3d11_texture_2d_description_cpu.Usage = 3
    d3d11_texture_2d_description_cpu.Format = d3d11_texture_2d_description.Format
    d3d11_texture_2d_description_cpu.BindFlags = 0
    d3d11_texture_2d_description_cpu.CPUAccessFlags = 131072
    d3d11_texture_2d_description_cpu.MiscFlags = 0

    d3d11_texture_2d_cpu = ctypes.POINTER(ID3D11Texture2D)()
    d3d_device.CreateTexture2D(
        ctypes.byref(d3d11_texture_2d_description_cpu), None, ctypes.byref(d3d11_texture_2d_cpu),
    )

    return d3d11_texture_2d_cpu


# ============================

class LUID(ctypes.Structure):
    _fields_ = [("LowPart", wintypes.DWORD), ("HighPart", wintypes.LONG)]


class DXGI_ADAPTER_DESC1(ctypes.Structure):
    _fields_ = [
        ("Description", wintypes.WCHAR * 128),
        ("VendorId", wintypes.UINT),
        ("DeviceId", wintypes.UINT),
        ("SubSysId", wintypes.UINT),
        ("Revision", wintypes.UINT),
        ("DedicatedVideoMemory", wintypes.ULARGE_INTEGER),
        ("DedicatedSystemMemory", wintypes.ULARGE_INTEGER),
        ("SharedSystemMemory", wintypes.ULARGE_INTEGER),
        ("AdapterLuid", LUID),
        ("Flags", wintypes.UINT),
    ]


class DXGI_OUTPUT_DESC(ctypes.Structure):
    _fields_ = [
        ("DeviceName", wintypes.WCHAR * 32),
        ("DesktopCoordinates", wintypes.RECT),
        ("AttachedToDesktop", wintypes.BOOL),
        ("Rotation", wintypes.UINT),
        ("Monitor", wintypes.HMONITOR),
    ]


class DXGI_OUTDUPL_POINTER_POSITION(ctypes.Structure):
    _fields_ = [("Position", wintypes.POINT), ("Visible", wintypes.BOOL)]


class DXGI_OUTDUPL_FRAME_INFO(ctypes.Structure):
    _fields_ = [
        ("LastPresentTime", wintypes.LARGE_INTEGER),
        ("LastMouseUpdateTime", wintypes.LARGE_INTEGER),
        ("AccumulatedFrames", wintypes.UINT),
        ("RectsCoalesced", wintypes.BOOL),
        ("ProtectedContentMaskedOut", wintypes.BOOL),
        ("PointerPosition", DXGI_OUTDUPL_POINTER_POSITION),
        ("TotalMetadataBufferSize", wintypes.UINT),
        ("PointerShapeBufferSize", wintypes.UINT),
    ]


class DXGI_MAPPED_RECT(ctypes.Structure):
    _fields_ = [("Pitch", wintypes.INT), ("pBits", ctypes.POINTER(wintypes.FLOAT))]


class IDXGIObject(comtypes.IUnknown):
    _iid_ = comtypes.GUID("{aec22fb8-76f3-4639-9be0-28eb43a67a2e}")
    _methods_ = [
        comtypes.STDMETHOD(comtypes.HRESULT, "SetPrivateData"),
        comtypes.STDMETHOD(comtypes.HRESULT, "SetPrivateDataInterface"),
        comtypes.STDMETHOD(comtypes.HRESULT, "GetPrivateData"),
        comtypes.STDMETHOD(comtypes.HRESULT, "GetParent"),
    ]


class IDXGIDeviceSubObject(IDXGIObject):
    _iid_ = comtypes.GUID("{3d3e0379-f9de-4d58-bb6c-18d62992f1a6}")
    _methods_ = [
        comtypes.STDMETHOD(comtypes.HRESULT, "GetDevice"),
    ]


class IDXGIResource(IDXGIDeviceSubObject):
    _iid_ = comtypes.GUID("{035f3ab4-482e-4e50-b41f-8a7f8bd8960b}")
    _methods_ = [
        comtypes.STDMETHOD(comtypes.HRESULT, "GetSharedHandle"),
        comtypes.STDMETHOD(comtypes.HRESULT, "GetUsage"),
        comtypes.STDMETHOD(comtypes.HRESULT, "SetEvictionPriority"),
        comtypes.STDMETHOD(comtypes.HRESULT, "GetEvictionPriority"),
    ]


class IDXGISurface(IDXGIDeviceSubObject):
    _iid_ = comtypes.GUID("{cafcb56c-6ac3-4889-bf47-9e23bbd260ec}")
    _methods_ = [
        comtypes.STDMETHOD(comtypes.HRESULT, "GetDesc"),
        comtypes.STDMETHOD(
            comtypes.HRESULT, "Map", [ctypes.POINTER(DXGI_MAPPED_RECT), wintypes.UINT]
        ),
        comtypes.STDMETHOD(comtypes.HRESULT, "Unmap"),
    ]


class IDXGIOutputDuplication(IDXGIObject):
    _iid_ = comtypes.GUID("{191cfac3-a341-470d-b26e-a864f428319c}")
    _methods_ = [
        comtypes.STDMETHOD(None, "GetDesc"),
        comtypes.STDMETHOD(
            comtypes.HRESULT,
            "AcquireNextFrame",
            [
                wintypes.UINT,
                ctypes.POINTER(DXGI_OUTDUPL_FRAME_INFO),
                ctypes.POINTER(ctypes.POINTER(IDXGIResource)),
            ],
        ),
        comtypes.STDMETHOD(comtypes.HRESULT, "GetFrameDirtyRects"),
        comtypes.STDMETHOD(comtypes.HRESULT, "GetFrameMoveRects"),
        comtypes.STDMETHOD(comtypes.HRESULT, "GetFramePointerShape"),
        comtypes.STDMETHOD(comtypes.HRESULT, "MapDesktopSurface"),
        comtypes.STDMETHOD(comtypes.HRESULT, "UnMapDesktopSurface"),
        comtypes.STDMETHOD(comtypes.HRESULT, "ReleaseFrame"),
    ]


class IDXGIOutput(IDXGIObject):
    _iid_ = comtypes.GUID("{ae02eedb-c735-4690-8d52-5a8dc20213aa}")
    _methods_ = [
        comtypes.STDMETHOD(comtypes.HRESULT, "GetDesc", [ctypes.POINTER(DXGI_OUTPUT_DESC)]),
        comtypes.STDMETHOD(comtypes.HRESULT, "GetDisplayModeList"),
        comtypes.STDMETHOD(comtypes.HRESULT, "FindClosestMatchingMode"),
        comtypes.STDMETHOD(comtypes.HRESULT, "WaitForVBlank"),
        comtypes.STDMETHOD(comtypes.HRESULT, "TakeOwnership"),
        comtypes.STDMETHOD(None, "ReleaseOwnership"),
        comtypes.STDMETHOD(comtypes.HRESULT, "GetGammaControlCapabilities"),
        comtypes.STDMETHOD(comtypes.HRESULT, "SetGammaControl"),
        comtypes.STDMETHOD(comtypes.HRESULT, "GetGammaControl"),
        comtypes.STDMETHOD(comtypes.HRESULT, "SetDisplaySurface"),
        comtypes.STDMETHOD(comtypes.HRESULT, "GetDisplaySurfaceData"),
        comtypes.STDMETHOD(comtypes.HRESULT, "GetFrameStatistics"),
    ]


class IDXGIOutput1(IDXGIOutput):
    _iid_ = comtypes.GUID("{00cddea8-939b-4b83-a340-a685226666cc}")
    _methods_ = [
        comtypes.STDMETHOD(comtypes.HRESULT, "GetDisplayModeList1"),
        comtypes.STDMETHOD(comtypes.HRESULT, "FindClosestMatchingMode1"),
        comtypes.STDMETHOD(comtypes.HRESULT, "GetDisplaySurfaceData1"),
        comtypes.STDMETHOD(
            comtypes.HRESULT,
            "DuplicateOutput",
            [
                ctypes.POINTER(ID3D11Device),
                ctypes.POINTER(ctypes.POINTER(IDXGIOutputDuplication)),
            ],
        ),
    ]


class IDXGIAdapter(IDXGIObject):
    _iid_ = comtypes.GUID("{2411e7e1-12ac-4ccf-bd14-9798e8534dc0}")
    _methods_ = [
        comtypes.STDMETHOD(
            comtypes.HRESULT,
            "EnumOutputs",
            [wintypes.UINT, ctypes.POINTER(ctypes.POINTER(IDXGIOutput))],
        ),
        comtypes.STDMETHOD(comtypes.HRESULT, "GetDesc"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CheckInterfaceSupport"),
    ]


class IDXGIAdapter1(IDXGIAdapter):
    _iid_ = comtypes.GUID("{29038f61-3839-4626-91fd-086879011a05}")
    _methods_ = [
        comtypes.STDMETHOD(comtypes.HRESULT, "GetDesc1", [ctypes.POINTER(DXGI_ADAPTER_DESC1)]),
    ]


class IDXGIFactory(IDXGIObject):
    _iid_ = comtypes.GUID("{7b7166ec-21c7-44ae-b21a-c9ae321ae369}")
    _methods_ = [
        comtypes.STDMETHOD(comtypes.HRESULT, "EnumAdapters"),
        comtypes.STDMETHOD(comtypes.HRESULT, "MakeWindowAssociation"),
        comtypes.STDMETHOD(comtypes.HRESULT, "GetWindowAssociation"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CreateSwapChain"),
        comtypes.STDMETHOD(comtypes.HRESULT, "CreateSoftwareAdapter"),
    ]


class IDXGIFactory1(IDXGIFactory):
    _iid_ = comtypes.GUID("{770aae78-f26f-4dba-a829-253c83d1b387}")
    _methods_ = [
        comtypes.STDMETHOD(
            comtypes.HRESULT,
            "EnumAdapters1",
            [ctypes.c_uint, ctypes.POINTER(ctypes.POINTER(IDXGIAdapter1))],
        ),
        comtypes.STDMETHOD(wintypes.BOOL, "IsCurrent"),
    ]


def initialize_dxgi_factory():
    create_factory_func = ctypes.windll.dxgi.CreateDXGIFactory1
    if sys.maxsize > 2 ** 32:
        create_factory_func.argtypes = (comtypes.GUID, ctypes.POINTER(ctypes.c_void_p))
    else:
        create_factory_func.argtypes = (ctypes.POINTER(comtypes.GUID), ctypes.POINTER(ctypes.c_void_p))
    create_factory_func.restype = ctypes.c_int32

    handle = ctypes.c_void_p(0)
    if sys.maxsize > 2 ** 32:
        create_factory_func(IDXGIFactory1._iid_, ctypes.byref(handle))
    else:
        create_factory_func(ctypes.byref(IDXGIFactory1._iid_), ctypes.byref(handle))
    idxgi_factory = ctypes.POINTER(IDXGIFactory1)(handle.value)

    return idxgi_factory


def discover_dxgi_adapters(dxgi_factory):
    dxgi_adapters = list()

    for i in range(0, 10):
        try:
            dxgi_adapter = ctypes.POINTER(IDXGIAdapter1)()
            dxgi_factory.EnumAdapters1(i, ctypes.byref(dxgi_adapter))

            dxgi_adapters.append(dxgi_adapter)
        except comtypes.COMError:
            break

    return dxgi_adapters


def describe_dxgi_adapter(dxgi_adapter):
    dxgi_adapter_description = DXGI_ADAPTER_DESC1()
    dxgi_adapter.GetDesc1(ctypes.byref(dxgi_adapter_description))

    return dxgi_adapter_description.Description


def discover_dxgi_outputs(dxgi_adapter):
    dxgi_outputs = list()

    for i in range(0, 10):
        try:
            dxgi_output = ctypes.POINTER(IDXGIOutput1)()
            dxgi_adapter.EnumOutputs(i, ctypes.byref(dxgi_output))

            dxgi_outputs.append(dxgi_output)
        except comtypes.COMError:
            break

    return dxgi_outputs


def describe_dxgi_output(dxgi_output):
    dxgi_output_description = DXGI_OUTPUT_DESC()
    dxgi_output.GetDesc(ctypes.byref(dxgi_output_description))

    rotation_mapping = {0: 0, 1: 0, 2: 90, 3: 180, 4: 270}

    return {
        "name": dxgi_output_description.DeviceName.split("\\")[-1],
        "position": {
            "left": dxgi_output_description.DesktopCoordinates.left,
            "top": dxgi_output_description.DesktopCoordinates.top,
            "right": dxgi_output_description.DesktopCoordinates.right,
            "bottom": dxgi_output_description.DesktopCoordinates.bottom,
        },
        "resolution": (
            (
                    dxgi_output_description.DesktopCoordinates.right
                    - dxgi_output_description.DesktopCoordinates.left
            ),
            (
                    dxgi_output_description.DesktopCoordinates.bottom
                    - dxgi_output_description.DesktopCoordinates.top
            ),
        ),
        "rotation": rotation_mapping.get(dxgi_output_description.Rotation, 0),
        "is_attached_to_desktop": bool(dxgi_output_description.AttachedToDesktop),
    }


def initialize_dxgi_output_duplication(dxgi_output, d3d_device):
    dxgi_output_duplication = ctypes.POINTER(IDXGIOutputDuplication)()
    dxgi_output.DuplicateOutput(d3d_device, ctypes.byref(dxgi_output_duplication))

    return dxgi_output_duplication


def get_dxgi_output_duplication_frame(dxgi_output_duplication, d3d_device, width=0, height=0):
    # 定义 DXGI 输出复制的帧信息和资源指针
    dxgi_output_duplication_frame_information = DXGI_OUTDUPL_FRAME_INFO()
    dxgi_resource = ctypes.POINTER(IDXGIResource)()

    # 尝试获取下一个帧
    dxgi_output_duplication.AcquireNextFrame(
        0,
        ctypes.byref(dxgi_output_duplication_frame_information),
        ctypes.byref(dxgi_resource),
    )

    frame = None

    # 如果捕获到有效的帧，则进行处理
    if dxgi_output_duplication_frame_information.LastPresentTime > 0:
        # 获取帧对应的2D纹理
        id3d11_texture_2d = dxgi_resource.QueryInterface(ID3D11Texture2D)
        # 准备CPU可读取的纹理
        id3d11_texture_2d_cpu = prepare_d3d11_texture_2d_for_cpu(id3d11_texture_2d, d3d_device)

        # 获取设备上下文并进行资源复制
        d3d_device_context = ctypes.POINTER(ID3D11DeviceContext)()
        d3d_device.GetImmediateContext(ctypes.byref(d3d_device_context))
        d3d_device_context.CopyResource(id3d11_texture_2d_cpu, id3d11_texture_2d)

        # 将纹理映射到内存
        id3d11_surface = id3d11_texture_2d_cpu.QueryInterface(IDXGISurface)
        dxgi_mapped_rect = DXGI_MAPPED_RECT()
        id3d11_surface.Map(ctypes.byref(dxgi_mapped_rect), 1)

        # 获取像素指针和步幅
        pointer = dxgi_mapped_rect.pBits
        pitch = int(dxgi_mapped_rect.Pitch)

        # 计算图像数据的大小（无旋转情况）
        size = pitch * height

        # 将图像数据拷贝到内存中
        frame = ctypes.string_at(pointer, size)

        # 解除映射
        id3d11_surface.Unmap()

    # 释放当前帧
    dxgi_output_duplication.ReleaseFrame()

    return frame


def capture(self):
    frame = None
    try:
        # 直接调用简化的获取帧函数
        frame = get_dxgi_output_duplication_frame(
            self.dxgi_output_duplication,
            self.d3d_device,
            width=self.resolution[0],
            height=self.resolution[1],
        )
    except:
        pass

    return frame


def get_dxgi_output_duplication_frame2(dxgi_output_duplication, d3d_device, width=0, height=0):
    # 定义 DXGI 输出复制的帧信息和资源指针
    dxgi_output_duplication_frame_information = DXGI_OUTDUPL_FRAME_INFO()
    dxgi_resource = ctypes.POINTER(IDXGIResource)()

    # 尝试获取下一个帧
    dxgi_output_duplication.AcquireNextFrame(
        300,
        ctypes.byref(dxgi_output_duplication_frame_information),
        ctypes.byref(dxgi_resource),
    )

    frame = None

    # 如果捕获到有效的帧，则进行处理
    if dxgi_output_duplication_frame_information.LastPresentTime > 0:
        # 获取帧对应的2D纹理
        id3d11_texture_2d = dxgi_resource.QueryInterface(ID3D11Texture2D)
        # 准备CPU可读取的纹理
        id3d11_texture_2d_cpu = prepare_d3d11_texture_2d_for_cpu(id3d11_texture_2d, d3d_device)

        # 获取设备上下文并进行资源复制
        d3d_device_context = ctypes.POINTER(ID3D11DeviceContext)()
        d3d_device.GetImmediateContext(ctypes.byref(d3d_device_context))
        d3d_device_context.CopyResource(id3d11_texture_2d_cpu, id3d11_texture_2d)

        # 将纹理映射到内存
        id3d11_surface = id3d11_texture_2d_cpu.QueryInterface(IDXGISurface)
        dxgi_mapped_rect = DXGI_MAPPED_RECT()
        id3d11_surface.Map(ctypes.byref(dxgi_mapped_rect), 1)

        # 获取像素指针和步幅
        pointer = dxgi_mapped_rect.pBits
        pitch = int(dxgi_mapped_rect.Pitch)

        # 计算图像数据的大小（无旋转情况）
        size = pitch * height

        # 将图像数据拷贝到内存中
        frame = ctypes.string_at(pointer, size)

        # 解除映射
        id3d11_surface.Unmap()

    # 释放当前帧
    dxgi_output_duplication.ReleaseFrame()

    return frame


def get_dxgi_output_duplication_frame(
        dxgi_output_duplication,
        d3d_device,
        process_func=None,
        width=0,
        height=0,
        region=None,
        rotation=0,
):
    dxgi_output_duplication_frame_information = DXGI_OUTDUPL_FRAME_INFO()
    dxgi_resource = ctypes.POINTER(IDXGIResource)()

    dxgi_output_duplication.AcquireNextFrame(
        0, ctypes.byref(dxgi_output_duplication_frame_information), ctypes.byref(dxgi_resource),
    )

    frame = None

    if dxgi_output_duplication_frame_information.LastPresentTime > 0:
        id3d11_texture_2d = dxgi_resource.QueryInterface(ID3D11Texture2D)
        id3d11_texture_2d_cpu = prepare_d3d11_texture_2d_for_cpu(id3d11_texture_2d, d3d_device)

        d3d_device_context = ctypes.POINTER(ID3D11DeviceContext)()
        d3d_device.GetImmediateContext(ctypes.byref(d3d_device_context))

        d3d_device_context.CopyResource(id3d11_texture_2d_cpu, id3d11_texture_2d)

        id3d11_surface = id3d11_texture_2d_cpu.QueryInterface(IDXGISurface)
        dxgi_mapped_rect = DXGI_MAPPED_RECT()

        id3d11_surface.Map(ctypes.byref(dxgi_mapped_rect), 1)

        pointer = dxgi_mapped_rect.pBits
        pitch = int(dxgi_mapped_rect.Pitch)

        if rotation in (0, 180):
            size = pitch * height
        else:
            size = pitch * width

        frame = process_func(pointer, pitch, size, width, height, region, rotation)

        id3d11_surface.Unmap()

    dxgi_output_duplication.ReleaseFrame()

    return frame


# ======================
class Display:
    def __init__(
            self,
            name=None,
            adapter_name=None,
            resolution=None,
            position=None,
            rotation=None,
            scale_factor=None,
            is_primary=False,
            hmonitor=None,
            dxgi_output=None,
            dxgi_adapter=None,
    ):
        self.name = name or "Unknown"
        self.adapter_name = adapter_name or "Unknown Adapter"

        self.resolution = resolution or (0, 0)

        self.position = position or {"left": 0, "top": 0, "right": 0, "bottom": 0}
        self.rotation = rotation or 0
        self.scale_factor = scale_factor or 1.0

        self.is_primary = is_primary
        self.hmonitor = hmonitor or 0

        self.dxgi_output = dxgi_output
        self.dxgi_adapter = dxgi_adapter

        self.d3d_device = None
        self.d3d_device_context = None

        self.dxgi_output_duplication = self._initialize_dxgi_output_duplication()

    def __repr__(self):
        return f"<Display name={self.name} adapter={self.adapter_name} resolution={self.resolution[0]}x{self.resolution[1]} rotation={self.rotation} scale_factor={self.scale_factor} primary={self.is_primary}>"

    def capture(self, process_func, region=None):
        region = self._get_clean_region(region)
        frame = None

        try:
            frame = get_dxgi_output_duplication_frame(
                self.dxgi_output_duplication,
                self.d3d_device,
                process_func=process_func,
                width=self.resolution[0],
                height=self.resolution[1],
                region=region,
                rotation=self.rotation,
            )
        except:
            pass

        return frame

    def _initialize_dxgi_output_duplication(self):
        (self.d3d_device, self.d3d_device_context,) = initialize_d3d_device(
            self.dxgi_adapter
        )

        return initialize_dxgi_output_duplication(
            self.dxgi_output, self.d3d_device
        )

    def _get_clean_region(self, region):
        if region is None:
            return (0, 0, self.resolution[0], self.resolution[1])

        clean_region = list()

        clean_region.append(0 if region[0] < 0 or region[0] > self.resolution[0] else region[0])
        clean_region.append(0 if region[1] < 0 or region[1] > self.resolution[1] else region[1])
        clean_region.append(
            self.resolution[0] if region[2] < 0 or region[2] > self.resolution[0] else region[2]
        )
        clean_region.append(
            self.resolution[1] if region[3] < 0 or region[3] > self.resolution[1] else region[3]
        )

        return tuple(clean_region)

    @classmethod
    def discover_displays(cls):
        display_device_name_mapping = get_display_device_name_mapping()

        dxgi_factory = initialize_dxgi_factory()
        dxgi_adapters = discover_dxgi_adapters(dxgi_factory)

        displays = list()

        for dxgi_adapter in dxgi_adapters:
            dxgi_adapter_description = describe_dxgi_adapter(dxgi_adapter)

            for dxgi_output in discover_dxgi_outputs(dxgi_adapter):
                dxgi_output_description = describe_dxgi_output(dxgi_output)

                if dxgi_output_description["is_attached_to_desktop"]:
                    display_device = display_device_name_mapping.get(
                        dxgi_output_description["name"]
                    )

                    if display_device is None:
                        display_device = ("Unknown", False)

                    hmonitor = get_hmonitor_by_point(
                        dxgi_output_description["position"]["left"],
                        dxgi_output_description["position"]["top"],
                    )

                    scale_factor = get_scale_factor_for_monitor(hmonitor)

                    display = cls(
                        name=display_device[0],
                        adapter_name=dxgi_adapter_description,
                        resolution=dxgi_output_description["resolution"],
                        position=dxgi_output_description["position"],
                        rotation=dxgi_output_description["rotation"],
                        scale_factor=scale_factor,
                        is_primary=display_device[1],
                        hmonitor=hmonitor,
                        dxgi_output=dxgi_output,
                        dxgi_adapter=dxgi_adapter,
                    )

                    displays.append(display)

        return displays


class DXGI:
    _displays = None
    _lock = threading.Lock()
    def __init__(self, hwnd=None, screen=0, fps=0):
        # 初始化 屏幕列表
        if DXGI._displays is None:
            displays = Display.discover_displays()
            DXGI._displays = displays
        else:
            displays = DXGI._displays
        # 获取屏幕句柄
        self.hwnd_desktop = user32.GetDesktopWindow()
        self.set_hwnd(hwnd)
        self.screen = screen

        if screen < len(displays):
            self.d = displays[screen]
        else:
            raise Exception(f"没有屏幕:{screen},请检查是否支持多屏幕")

        self.error_max_refresh = 10
        if self.d.resolution[0] <= 0 or self.d.resolution[1] <= 0:
            raise Exception("无效的分辨率，width 和 height 应为正数")
        if not self.d.d3d_device or not self.d.dxgi_output_duplication:
            raise Exception("D3D 设备或 DXGI 输出复制对象未正确初始化")
        self.t_for_capture = None
        self._t_for_capture = None
        self._fps = fps
        self.for_capture()
        while True:
            time.sleep(0.01)
            if not getattr(self, "image", None) is None:
                break
    def __del__(self):
        """
        清理 DXGI 相关的资源，停止 DXGI 操作。
        """
        try:
            self._t_for_capture = None
            self.t_for_capture = None
            if self.d.dxgi_output_duplication:
                self.d.dxgi_output_duplication.ReleaseFrame()
                print("释放帧")
        except Exception as e:
            pass

    def for_capture(self):
        def func():
            self._t_for_capture = True
            while self._t_for_capture:
                s = time.time()
                self.image = self._capture()
                if self._fps:
                    delay = 1 / self._fps - (time.time() - s)
                    if delay > 0:
                        time.sleep(delay)
        if self.t_for_capture is None:
            self.t_for_capture = threading.Thread(target=func,daemon=True)
            self.t_for_capture.start()

    def set_hwnd(self,hwnd):
        if hwnd is None:
            self.hwnd = self.hwnd_desktop
        else:
            self.hwnd = hwnd
        self.width, self.height = Window.GetClientSize(self.hwnd)
        if self.width <= 0 or self.height <= 0:
            raise Exception("无效的分辨率，width 和 height 应为正数")
    def _capture(self):
        frame = None
        s = time.time()
        with DXGI._lock:
            while frame is None:
                try:
                    frame = get_dxgi_output_duplication_frame2(
                        self.d.dxgi_output_duplication,
                        self.d.d3d_device,
                        width=self.d.resolution[0],
                        height=self.d.resolution[1],
                    )
                except Exception as e:
                    pass
                    if time.time() - s > self.error_max_refresh:
                        raise Exception("截图超时,报错:%s" %e)
            # frame = get_dxgi_output_duplication_frame2(
            #         self.d.dxgi_output_duplication,
            #         self.d.d3d_device,
            #         width=self.d.resolution[0],
            #         height=self.d.resolution[1],
            #     )
            img = dxpyd.MiNiNumPy.bytes_bgra_to_arr3d(frame, self.d.resolution[1], self.d.resolution[0])
            h,w = img.shape[:2]
            if h == 0 or w == 0:
                raise Exception("截图失败,截图为空")
            return img
    def capture(self, x1: int = None, y1: int = None, x2: int = None, y2: int = None):

        if x1 is None or x1 < 0:
            x1 = 0
        if y1 is None or y1 < 0:
            y1 = 0
        if x2 is None or x2 > self.width:
            x2 = self.width
        if y2 is None or y2 > self.height:
            y2 = self.height
        image = self.image
        if self.hwnd != self.hwnd_desktop:
            x3, y3 = Window.ClientToScreen(self.hwnd, x1, y1)
            x4, y4 = Window.ClientToScreen(self.hwnd, x2, y2)
            if x3 < 0:
                x3 = 0
            if y3 < 0:
                y3 = 0
            if x3 > self.d.resolution[0] or y3 > self.d.resolution[1]:
                raise ValueError("截图越界,窗口左上角不显示在屏幕上")
            if x4 < 0:
                raise ValueError("截图越界,窗口右下角不显示在屏幕上")
            if y4 < 0:
                raise ValueError("截图越界,窗口右下角不显示在屏幕上")
            if x4 > self.d.resolution[0]:
                x4 = self.d.resolution[0]
            if y4 > self.d.resolution[1]:
                y4 = self.d.resolution[1]

            image = image[y3:y4, x3:x4]  # 截图句柄窗口
        else:
            image = image[y1:y2, x1:x2]
        return image  # 如果有裁剪，则非连续内存
if __name__ == '__main__':
    from dxGame import DXKM
    dx = DXGI(787764)
    km = DXKM(787764)
    km.MoveTo(100,100)
    while True:
        image = dx.Capture()
